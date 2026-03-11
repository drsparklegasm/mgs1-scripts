-- debug-radio-offsets.lua
-- PCSX-Redux Lua debugger script for MGS1 patched SLPM_861.11
-- Monitors all patched offset locations in the radio codec interpreter.
-- Load via Debug > Lua editor in PCSX-Redux, then click Run.
--
-- Usage:
--   PAUSE_ON_HIT = true   -- pause emulator on each breakpoint hit
--   PAUSE_ON_HIT = false  -- log only (default, less intrusive)
--   VERBOSE = true        -- log trampoline internals too
--   Call disableAll() / enableAll() from Lua console to toggle

-- ============================================================
-- Config
-- ============================================================
PAUSE_ON_HIT = false
VERBOSE = false          -- set true to also log trampoline guts
MAX_LOG_LINES = 500      -- stop logging after this many hits
LOG_TO_FILE = false      -- set true to write debug-radio.log
-- ============================================================

local logCount = 0
local logFile = nil

if LOG_TO_FILE then
    logFile = io.open("debug-radio.log", "w")
end

local function log(msg)
    if logCount >= MAX_LOG_LINES then return end
    logCount = logCount + 1
    local line = string.format("[%d] %s", logCount, msg)
    print(line)
    if logFile then logFile:write(line .. "\n"); logFile:flush() end
end

local function hex(val)
    if val == nil then return "nil" end
    return string.format("0x%08X", val)
end

local function dumpRegs(label)
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("--- %s ---", label))
    log(string.format("  PC=%s  s0=%s  s1=%s  s3=%s  s4=%s",
        hex(regs.pc), hex(g.s0), hex(g.s1), hex(g.s3), hex(g.s4)))
    log(string.format("  v0=%s  v1=%s  a0=%s  a1=%s  ra=%s",
        hex(g.v0), hex(g.v1), hex(g.a0), hex(g.a1), hex(g.ra)))
end

local function readMemByte(addr)
    local phys = bit.band(addr, 0x1FFFFF)
    local mem = PCSX.getMemPtr()
    return mem[phys]
end

local function readMemWord(addr)
    local phys = bit.band(addr, 0x1FFFFF)
    local mem = PCSX.getMemPtr()
    -- Little-endian 32-bit read
    return mem[phys]
         + mem[phys + 1] * 0x100
         + mem[phys + 2] * 0x10000
         + mem[phys + 3] * 0x1000000
end

local function dumpBytes(addr, count)
    local parts = {}
    for i = 0, count - 1 do
        table.insert(parts, string.format("%02X", readMemByte(addr + i)))
    end
    return table.concat(parts, " ")
end

-- Store all breakpoint objects so they don't get GC'd
local bps = {}

local function bp(addr, cause, callback)
    local b = PCSX.addBreakpoint(addr, 'Exec', 4, cause, function(a, w, c)
        callback()
        if PAUSE_ON_HIT then
            PCSX.pauseEmulator()
        end
    end)
    table.insert(bps, b)
    return b
end

-- ============================================================
-- menu_gcl_exec_block — 0x800486C8
-- The main radio script interpreter
-- ============================================================

bp(0x800486C8, "exec_block ENTRY", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format(">> exec_block ENTRY  s3(pScript)=%s  bytes: %s",
        hex(g.s3), dumpBytes(g.s3, 10)))
end)

-- Patch A: addiu $s1, $s3, 5 — payload pointer
bp(0x800486E0, "Patch A: payload ptr", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [A] s1=s3+5  s3=%s -> s1 will be %s",
        hex(g.s3), hex(g.s3 + 5)))
end)

-- Patch B: j trampoline_B — 4-byte block size read
bp(0x800486F0, "Patch B: j trampoline_B", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [B] JUMP to trampoline_B  s3=%s  pScript bytes: %s",
        hex(g.s3), dumpBytes(g.s3, 8)))
end)

-- After trampoline returns: beq $a0, $zero + delay slot sets $s4
bp(0x80048700, "Post-B: beq check", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [B ret] a0(1st payload byte)=%s  s4(block size)=%s  s1=%s",
        hex(g.a0), hex(g.s4), hex(g.s1)))
    if g.a0 == 0 then
        log("   *** a0=0 -> will EXIT block ***")
    end
end)

-- Patch C: jal read_dword for 0xFF cmd size
bp(0x8004871C, "Patch C: jal read_dword (0xFF)", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [C] read_dword call  a0(out)=%s  a1(data)=%s  bytes@a1: %s",
        hex(g.a0), hex(g.a1), dumpBytes(g.a1, 6)))
end)

-- After read_dword: $s1 = $v0 (ptr past 4-byte size)
bp(0x80048724, "Post-C: s1 = v0", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [C ret] v0(ptr past size)=%s -> s1",
        hex(g.v0)))
end)

-- Load 32-bit size from stack
bp(0x80048850, "lw size from stack", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    local sp = g.sp
    local stackVal = readMemWord(sp + 16)
    log(string.format("   [stack] sp=%s  [sp+16]=%s (32-bit size)",
        hex(sp), hex(stackVal)))
end)

-- Patch D: addiu $v0, $v0, -4 (advance distance)
bp(0x80048858, "Patch D: v0 = size-4", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [D] v0(size)=%s -> v0-4=%s",
        hex(g.v0), hex(g.v0 - 4)))
end)

-- Advance past sub-command payload
bp(0x80048860, "Post-D: s1 advance", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [D done] s1=%s + v0=%s -> next=%s",
        hex(g.s1), hex(g.v0), hex(g.s1 + g.v0)))
end)

-- ============================================================
-- radio_moveToNext — 0x8004868C
-- ============================================================

bp(0x8004868C, "moveToNext ENTRY", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format(">> moveToNext ENTRY  s0(base)=%s  bytes: %s",
        hex(g.s0), dumpBytes(g.s0, 8)))
end)

-- Patch E: jal read_dword
bp(0x800486A0, "Patch E: jal read_dword", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [E] read_dword  a0(out)=%s  a1(data)=%s  bytes@a1: %s",
        hex(g.a0), hex(g.a1), dumpBytes(g.a1, 6)))
end)

-- After read: lw $v0, 16($sp)
bp(0x800486A8, "Post-E: load size", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    local sp = g.sp
    local stackVal = readMemWord(sp + 16)
    log(string.format("   [E ret] [sp+16]=%s  s0=%s",
        hex(stackVal), hex(g.s0)))
end)

-- Return pointer: $v0 = $s0 + size
bp(0x800486B0, "Post-E: return ptr", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [E done] v0=%s  s0=%s  result=%s",
        hex(g.v0), hex(g.s0), hex(g.s0 + g.v0)))
end)

-- ============================================================
-- menu_radio_codec_task_proc — font address setup
-- ============================================================

-- Patch F: j trampoline_F (4-byte font offset read)
bp(0x800489FC, "Patch F: j trampoline_F", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format(">> [F] FONT OFFSET  s0(radioDatIter)=%s  bytes: %s",
        hex(g.s0), dumpBytes(g.s0, 8)))
end)

-- After trampoline: addiu $a1, $a1, 1
bp(0x80048A0C, "Post-F: a1 = size+1", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [F ret] a1(32-bit size)=%s -> a1+1=%s  s0=%s",
        hex(g.a1), hex(g.a1 + 1), hex(g.s0)))
end)

-- jal font_set_font_addr
bp(0x80048A10, "font_set_font_addr call", function()
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("   [F font] font_set_font_addr(1, s0+a1)  a1=%s  s0=%s  target=%s",
        hex(g.a1), hex(g.s0), hex(g.s0 + g.a1)))
end)

-- ============================================================
-- Trampolines (verbose mode only)
-- ============================================================

if VERBOSE then
    -- trampoline_B entry
    bp(0x800AA138, "tramp_B entry", function()
        local regs = PCSX.getRegisters()
        local g = regs.GPR.n
        log(string.format("   [tramp_B] s3=%s  bytes[1..5]: %s",
            hex(g.s3), dumpBytes(g.s3 + 1, 5)))
    end)

    -- trampoline_B exit
    bp(0x800AA160, "tramp_B exit", function()
        local regs = PCSX.getRegisters()
        local g = regs.GPR.n
        log(string.format("   [tramp_B done] v0=%s  a0=%s  s4=%s",
            hex(g.v0), hex(g.a0), hex(g.s4)))
    end)

    -- trampoline_C (read_dword) entry
    bp(0x800AA168, "tramp_C entry", function()
        local regs = PCSX.getRegisters()
        local g = regs.GPR.n
        log(string.format("   [tramp_C] a0(out)=%s  a1(data)=%s  bytes: %s",
            hex(g.a0), hex(g.a1), dumpBytes(g.a1, 4)))
    end)

    -- trampoline_C result
    bp(0x800AA190, "tramp_C result", function()
        local regs = PCSX.getRegisters()
        local g = regs.GPR.n
        log(string.format("   [tramp_C done] v1(32-bit val)=%s  v0(ptr+4)=%s",
            hex(g.v1), hex(g.v0)))
    end)

    -- trampoline_F entry
    bp(0x800AA19C, "tramp_F entry", function()
        local regs = PCSX.getRegisters()
        local g = regs.GPR.n
        log(string.format("   [tramp_F] s0=%s  bytes[1..4]: %s",
            hex(g.s0), dumpBytes(g.s0 + 1, 4)))
    end)

    -- trampoline_F result
    bp(0x800AA1C0, "tramp_F result", function()
        local regs = PCSX.getRegisters()
        local g = regs.GPR.n
        log(string.format("   [tramp_F done] a1(32-bit size)=%s",
            hex(g.a1)))
    end)
end

-- ============================================================
-- Trampoline integrity watchdog
-- Uses WRITE breakpoints on the trampoline memory regions.
-- When anything writes to trampoline space, we log WHO and WHAT.
-- ============================================================

-- Expected bytes for each trampoline (from patch_slpm86111.py)
local TRAMP_EXPECTED = {
    { name = "trampoline_B", addr = 0x800AA138, words = {
        0x92620001, 0x92630002, 0x00021200, 0x00621025,
        0x92630003, 0x00021200, 0x00621025, 0x92630004,
        0x00021200, 0x92640005, 0x080121C0, 0x00000000,
    }},
    { name = "trampoline_C", addr = 0x800AA168, words = {
        0x90A20000, 0x90A30001, 0x00021200, 0x00621025,
        0x90A30002, 0x00021200, 0x00621025, 0x90A30003,
        0x00021200, 0x00621825, 0x24A20004, 0x03E00008,
        0xAC830000,
    }},
    { name = "trampoline_F", addr = 0x800AA19C, words = {
        0x92020001, 0x92050002, 0x00021200, 0x00A21025,
        0x92050003, 0x00021200, 0x00A21025, 0x92050004,
        0x00021200, 0x00A22825, 0x08012283, 0x00000000,
    }},
}

-- Write watchpoints on full trampoline region (0x800AA138 .. 0x800AA1CB)
local TRAMP_REGION_START = 0x800AA138
local TRAMP_REGION_SIZE  = 0x800AA1CC - 0x800AA138  -- covers B+C+F

local watchBp = PCSX.addBreakpoint(TRAMP_REGION_START, 'Write', TRAMP_REGION_SIZE,
    'TRAMPOLINE WRITE DETECTED', function(address, width, cause)
    local regs = PCSX.getRegisters()
    local g = regs.GPR.n
    log(string.format("!!! TRAMPOLINE WRITE at %s width=%d  PC=%s  ra=%s",
        hex(address), width, hex(regs.pc), hex(g.ra)))
    log(string.format("    v0=%s  v1=%s  a0=%s  a1=%s  a2=%s  a3=%s",
        hex(g.v0), hex(g.v1), hex(g.a0), hex(g.a1), hex(g.a2), hex(g.a3)))
    log(string.format("    s0=%s  s1=%s  s2=%s  s3=%s  t0=%s  t1=%s",
        hex(g.s0), hex(g.s1), hex(g.s2), hex(g.s3), hex(g.t0), hex(g.t1)))
    -- Always pause on trampoline corruption so we can inspect
    PCSX.pauseEmulator()
end)
table.insert(bps, watchBp)

-- Manual integrity check — call from Lua console anytime
function checkTrampolines()
    local allOk = true
    for _, tramp in ipairs(TRAMP_EXPECTED) do
        local corrupted = {}
        for i, expected in ipairs(tramp.words) do
            local addr = tramp.addr + (i - 1) * 4
            local actual = readMemWord(addr)
            if actual ~= expected then
                table.insert(corrupted, string.format(
                    "  %s: expected 0x%08X got 0x%08X",
                    hex(addr), expected, actual))
                allOk = false
            end
        end
        if #corrupted > 0 then
            print(string.format("CORRUPT: %s (%d/%d words wrong)",
                tramp.name, #corrupted, #tramp.words))
            for _, line in ipairs(corrupted) do print(line) end
        else
            print(string.format("OK: %s (%d words verified)", tramp.name, #tramp.words))
        end
    end
    if allOk then
        print("All trampolines intact.")
    else
        print("*** CORRUPTION DETECTED — see above ***")
    end
    return allOk
end

-- ============================================================
-- Utility functions (call from Lua console)
-- ============================================================

function disableAll()
    for _, b in ipairs(bps) do b:disable() end
    print("All radio debug breakpoints DISABLED (including write watch)")
end

function enableAll()
    for _, b in ipairs(bps) do b:enable() end
    print("All radio debug breakpoints ENABLED (including write watch)")
end

function resetLog()
    logCount = 0
    print("Log counter reset")
end

function status()
    print(string.format("Breakpoints: %d | Log lines: %d/%d | Pause: %s | Verbose: %s",
        #bps, logCount, MAX_LOG_LINES,
        tostring(PAUSE_ON_HIT), tostring(VERBOSE)))
end

-- ============================================================
print(string.format("=== MGS1 Radio Offset Debugger loaded ==="))
print(string.format("  %d breakpoints set (%d exec + 1 write watch)", #bps, #bps - 1))
print(string.format("  PAUSE_ON_HIT = %s", tostring(PAUSE_ON_HIT)))
print(string.format("  VERBOSE = %s (trampoline internals)", tostring(VERBOSE)))
print("  Write watchpoint on 0x800AA138-0x800AA1CB (all trampolines)")
print("  Commands: disableAll() enableAll() resetLog() status()")
print("            checkTrampolines()  -- manual integrity check")
print("  Tip: set PAUSE_ON_HIT=true then enableAll() to step through")
print("===========================================")