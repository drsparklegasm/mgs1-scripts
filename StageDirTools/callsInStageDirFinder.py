import os, struct
import argparse
import json

import progressbar

# filename = "radioDatFiles/STAGE-usa-d1.DIR"

FREQ_LIST = [
    b'\x37\x05', # 140.85, Campbell
    b'\x37\x10', # 140.96, Mei Ling
    b'\x36\xbf', # 140.15, Meryl
    b'\x37\x20', # 141.12, Otacon
    b'\x37\x48', # 141.52, Nastasha
    b'\x37\x64', # 141.80, Miller
    b'\x36\xE0', # 140.48, Deepthroat
    b'\x36\xb7',  # 140.07, Staff, Integral exclusive
    b'\x36\xbb',
    b'\x36\xbc',
    bytes.fromhex('36bb'),
    bytes.fromhex('36bc'), # 140.12, ????
    b'\x37\xac', # 142.52, Nastasha? ACCIDENT
]

FREQ_NAMES = {
    0x3705: "Campbell  (140.85)",
    0x3710: "Mei Ling  (140.96)",
    0x36BF: "Meryl     (140.15)",
    0x3720: "Otacon    (141.12)",
    0x3748: "Nastasha  (141.52)",
    0x3764: "Miller    (141.80)",
    0x36E0: "Deepthroat(140.48)",
    0x36B7: "Staff     (140.07)",
    0x36BB: "???       (140.11)",
    0x36BC: "???       (140.12)",
    0x37AC: "Nastasha? (142.52)",
}

USE_LONG = False
INTEGRAL = False  # When True, radio offsets are 2-byte block indices at bytes[6:8] (* 0x800)

# This dict will have {stageOffset: [ callOffset int, hexstr ] } to be updated later.
offsetDict: dict[int, tuple[int, str]] = {}
filesize = 0
stageData = b''
debug = False
outputFileToggle = False

# TOC: list of (name, start_byte, end_byte) tuples, sorted by start_byte
stageTOC: list[tuple[str, int, int]] = []

def parseTOC():
    """
    Parse the STAGE.DIR table of contents.
    Format (all little-endian):
      [0x00-0x03] fileListSize (N * 0x0C)
      [0x04 ...] N folder entries, each 12 bytes:
        [0x00-0x07] folder name (zero-padded ASCII)
        [0x08-0x0B] block offset (actual byte offset = block * 0x800)
    Populates stageTOC with (name, start_byte, end_byte) tuples.
    """
    global stageTOC, stageData, filesize

    list_size = struct.unpack_from('<I', stageData, 0)[0]
    num_entries = list_size // 12

    entries = []
    for i in range(num_entries):
        base = 4 + i * 12
        name = stageData[base:base + 8].rstrip(b'\x00').decode('ascii', errors='replace')
        block = struct.unpack_from('<I', stageData, base + 8)[0]
        byte_off = block * 0x800
        entries.append((name, byte_off))

    # Build TOC with end boundaries (each folder ends where the next begins, last ends at EOF)
    stageTOC = []
    for i, (name, start) in enumerate(entries):
        if i + 1 < len(entries):
            end = entries[i + 1][1]
        else:
            end = filesize
        stageTOC.append((name, start, end))

def getStageForOffset(byte_offset: int) -> str:
    """Return the stage folder name that contains the given byte offset."""
    for name, start, end in stageTOC:
        if start <= byte_offset < end:
            return name
    return "???"

def printTOC():
    """Print the full stage TOC."""
    print("\n========== STAGE.DIR TABLE OF CONTENTS ==========")
    print("{:<12} {:>8} {:>12} {:>12} {:>10}".format(
        "Stage", "Block", "Start", "End", "Size"))
    print("-" * 60)
    for name, start, end in stageTOC:
        block = start // 0x800
        size = end - start
        print("{:<12} {:>8} 0x{:08X} 0x{:08X} {:>10}".format(
            name, block, start, end, size))
    print("  Total stages: {}".format(len(stageTOC)))

def checkFreq(offset):
    global stageData

    if stageData[offset + 1 : offset + 3] in FREQ_LIST:
        return True
    else:
        return False

def writeCall(offset):
    global stageData
    global FREQ_LIST
    global outputFileToggle
    global INTEGRAL

    callHex = stageData[offset + 4: offset + 8].hex()
    if INTEGRAL:
        # Integral: 2-byte big-endian block index at bytes[6:7], byte offset = block * 0x800
        block = struct.unpack('>H', stageData[offset + 6: offset + 8])[0]
        callInt = str(block * 0x800)
    else:
        # USA/JPN: 3-byte big-endian byte offset at bytes[5:7]
        callInt = str(struct.unpack('>L', b'\x00' + stageData[offset + 5: offset + 8])[0])
    offsetDict.update({offset: (callInt, callHex)})

    # Write to output file:
    if outputFileToggle:

        writeString = f'{offset},'                                                          # Offset in stage.dir
        writeString += stageData[offset: offset + 4].hex() + ","                            # Offset of the frequency as it appears in hex
        writeString += str(struct.unpack('>h', stageData[offset + 1: offset + 3])[0]) + "," # Call Frequency
        writeString += f'{callHex},{callInt},\n'                                            # offset (hex, int) of call in Radio.dat
        output.write(writeString)

# For now this will just get all offsets of radio calls in the stage.dir and write a CSV file with the relevent offsets.
def getCallOffsets():
    global filesize

    offset = 0
    bar = progressbar.ProgressBar(maxval=filesize)
    bar.start()

    while offset < filesize:
        # Check for \x01 first, then check for a call
        if stageData[offset].to_bytes() == b'\x01' and stageData[offset + 3].to_bytes() == b'\x0a': # After running without this, seems all call offsets DO have 0x0a in the 4th byte
            if checkFreq(offset): # We only write the call to the csv if the call matches a frequency, this check might not be needed....?
                writeCall(offset)
        offset += 1 # No matter what we increase offset in all scenarios
        bar.update(offset)
    bar.finish()

def printCallsByStage():
    """
    Print all found radio call references grouped by the stage they appear in,
    showing the raw 8-byte match, frequency, and RADIO.DAT offset.
    """
    if not stageTOC:
        print("(no TOC parsed, skipping stage grouping)")
        return

    # Group calls by stage
    calls_by_stage: dict[str, list] = {}
    for pos in sorted(offsetDict.keys()):
        stage = getStageForOffset(pos)
        if stage not in calls_by_stage:
            calls_by_stage[stage] = []
        call_int_str, call_hex = offsetDict[pos]
        freq_val = struct.unpack('>H', stageData[pos + 1: pos + 3])[0]
        freq_name = FREQ_NAMES.get(freq_val, "unknown   ({:.2f})".format(freq_val / 100))
        aligned = "(0x800-aligned)" if int(call_int_str) % 0x800 == 0 else "(NOT aligned)"
        calls_by_stage[stage].append((pos, freq_name, call_int_str, call_hex, aligned))

    print("\n========== RADIO CALLS BY STAGE ==========")
    for stage_name, start, end in stageTOC:
        if stage_name not in calls_by_stage:
            continue
        calls = calls_by_stage[stage_name]
        print("\n  --- {} (0x{:08X} - 0x{:08X}, {} calls) ---".format(
            stage_name, start, end, len(calls)))
        for pos, freq_name, call_int, call_hex, aligned in calls:
            print("    pos: 0x{:08X}  {}  radio_off: {} (0x{:06X})  raw: {}  {}".format(
                pos, freq_name, call_int, int(call_int), call_hex, aligned))

    total = sum(len(v) for v in calls_by_stage.values())
    stages_with_calls = len(calls_by_stage)
    print("\n  Total: {} call refs across {} stages".format(total, stages_with_calls))


def main(args=None):
    global stageData
    global filesize
    global outputFileToggle

    stageData = stageDir.read() # The byte stream is better to use than the file on disk if you can.
    filesize = len(stageData)

    parseTOC()
    printTOC()

    # Write csv header
    output.write('offset,call hex,frequency,call data offset\n')

    # Main used to just be getting the call offsets
    getCallOffsets()
    printCallsByStage()
    print('Finished checking for calls in STAGE.DIR!')
    output.close()

    with open("callOffsetDict.json", 'w') as f:
        f.write(json.dumps(offsetDict))
        f.close

if __name__ == "__main__":

    # We should get args from user. Using argParse
    parser = argparse.ArgumentParser(description=f'Search a GCX file for RADIO.DAT codec calls')
    # REQUIRED
    parser.add_argument('filename', type=str, help="The GCX file to Search. Can be RADIO.DAT or a portion of it.")
    parser.add_argument('output', nargs="?", type=str, help="Output Filename (.txt)")

    args = parser.parse_args()

    # Args parsed
    filename: str = args.filename

    stageName = filename.split('/')[-2]
    stageFile = filename.split('/')[-1].split(".")[0]

    print(f'{stageName}/{stageFile}')

    if args.output:
        outputFile = args.output
        outputFileToggle = True
    else:
        outputFile = f'stageAnalysis-jpn/{stageName}-{stageFile}.csv'
    
    stageDir = open(filename, 'rb')
    output = open(outputFile, 'w')
    
    main()

def init(filename: str):
    global filesize
    global stageData
    global USE_LONG

    stageDir = open(filename, 'rb')
    stageData = stageDir.read()
    filesize = len(stageData)

    parseTOC()
    if debug:
        printTOC()

    print(f'Getting STAGE.DIR call offsets... please be patient!')
    getCallOffsets()

    if debug:
        printCallsByStage()

    print('Finished checking for calls in STAGE.DIR! Ready to proceed.')