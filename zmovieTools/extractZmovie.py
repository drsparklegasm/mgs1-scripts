"""
Extract and recompile subtitle data from ZMOVIE.STR entirely in-memory.

Output JSON format (same as extractDemoVox.py):
  {"zmovie-00": {"1234": {"duration": "5678", "text": "..."}}, ...}
  Only entries that contain subtitles are included.

Usage (module):
    from zmovieTools.extractZmovie import extractFromFile, compileToFile
    data = extractFromFile("ZMOVIE.STR")
    compileToFile("OUT.STR", original_bytes, edited_json)
"""

import os, sys, re, struct

_here    = os.path.dirname(os.path.abspath(__file__))
_scripts = os.path.dirname(_here)
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

import translation.radioDict as RD

ZMOVIE_BLOCK   = 0x920   # sector alignment for zmovie (vs 0x800 for demo/vox)
NUM_ENTRIES    = 4       # hardcoded in movieSplitter.py
SUBTITLE_PATCH_LIMIT = 0x800  # subtitle section padded to this within each entry

# CD-ROM raw sector reconstruction constants
_CD_SYNC = bytes([0x00] + [0xFF] * 10 + [0x00])  # 12-byte sync pattern
_RAW_SECTOR_SIZE = 2352
_XA_SUBHEADER_SIZE = 8     # subheader repeated twice at start of each 0x920 block
_XA_PAYLOAD_SIZE = ZMOVIE_BLOCK - _XA_SUBHEADER_SIZE  # 2328 bytes

# Pattern used by movieSplitter.py to locate subtitle blocks
_SUBTITLE_RE = re.compile(b'\x02\x00\x00\x00......\x10\x00', re.DOTALL)


# ── TOC ──────────────────────────────────────────────────────────────────────

def getEntryOffsets(data: bytes) -> list:
    """
    Parse the TOC (first ZMOVIE_BLOCK bytes) and return byte offsets for each
    zmovie entry.  Offsets are stored in the TOC as block numbers; multiply by
    ZMOVIE_BLOCK to get byte offsets.
    """
    toc    = data[:ZMOVIE_BLOCK]
    cursor = 16
    offsets = []
    for _ in range(NUM_ENTRIES):
        block_num = struct.unpack("<I", toc[cursor:cursor + 4])[0]
        offsets.append(block_num * ZMOVIE_BLOCK)
        cursor += 8
    return offsets


# ── Subtitle extraction ───────────────────────────────────────────────────────

def _parseTextBlock(data: bytes) -> tuple:
    """
    Parse the subtitle text area for one zmovie entry.
    `data` starts at offset+16 relative to the subtitle-block match (the 16-byte
    header at the match start is already skipped by the caller).

    Returns (texts: list[str], coords: list[str]).
    coords entries are "startFrame,duration" strings.
    """
    segments = []
    coords   = []
    offset   = 0

    while offset < len(data):
        if data[offset] == 0x00:
            # Last subtitle entry — length bytes are null; find end by scanning.
            lastEnd = data.find(b'\x00', offset + 16)
            if lastEnd < 0:
                break
            raw     = data[offset:lastEnd]
            pad     = 4 - (len(raw) % 4)
            textSize = len(raw) + pad
            appearTime     = struct.unpack("I", data[offset + 4: offset + 8])[0]
            appearDuration = struct.unpack("I", data[offset + 8: offset + 12])[0]
            coords.append(f'{appearTime},{appearDuration}')
            segments.append(data[offset + 16: offset + textSize])
            break
        else:
            textSize = struct.unpack('<H', data[offset:offset + 2])[0]
            if textSize == 0:
                break
            appearTime     = struct.unpack("I", data[offset + 4: offset + 8])[0]
            appearDuration = struct.unpack("I", data[offset + 8: offset + 12])[0]
            segments.append(data[offset + 16: offset + textSize])
            coords.append(f'{appearTime},{appearDuration}')
            offset += textSize

    texts = []
    for seg in segments:
        text = RD.translateJapaneseHex(seg, {})
        texts.append(text.replace('\x00', ''))

    return texts, coords


def _extractEntrySubtitles(entryData: bytes) -> dict:
    """
    Find all subtitle blocks in one zmovie entry and return a merged dict:
      {startFrame_str: {"duration": str, "text": str}}
    """
    matches = _SUBTITLE_RE.finditer(entryData)
    valid_offsets = [
        m.start() for m in matches
        if entryData[m.start() + 28: m.start() + 32] == b'\x00\x00\x00\x00'
    ]

    result = {}
    for off in valid_offsets:
        subset = entryData[off + 16: off + 0x7e0]
        texts, coords = _parseTextBlock(subset)
        for text, timing_str in zip(texts, coords):
            startFrame, duration = timing_str.split(",")
            result[startFrame] = {"duration": duration, "text": text}

    return result


def extractFromFile(inputPath: str) -> dict:
    """
    Extract all subtitle data from ZMOVIE.STR without writing any intermediate files.

    Returns
    -------
    dict
        Keyed by entry name ("zmovie-00" … "zmovie-03").
        Only entries that contain subtitles are included.
    """
    with open(inputPath, 'rb') as f:
        data = f.read()

    offsets = getEntryOffsets(data)
    offsets.append(len(data))  # sentinel for slicing the last entry

    result = {}
    for i in range(len(offsets) - 1):
        start, end = offsets[i], offsets[i + 1]
        if start >= len(data):
            break
        key  = f"zmovie-{i:02}"
        subs = _extractEntrySubtitles(data[start:end])
        if subs:
            result[key] = subs
        print(f"  {key}: {len(subs)} subtitle(s) found.")

    return result


# ── Compilation ───────────────────────────────────────────────────────────────

def _encodeSubtitle(startFrame: int, duration: int, text: str) -> bytes:
    """
    Encode one subtitle as bytes.
    Mirrors common/structs.subtitle.__bytes__ without the class import.
    """
    encoded = RD.encodeJapaneseHex(text)[0]
    raw     = struct.pack("III", startFrame, duration, 0) + encoded
    pad     = 4 - (len(raw) % 4)
    return raw + bytes(pad)


def _buildSubBlock(subtitlesJson: dict) -> bytes:
    """
    Build the full subtitle block bytes from a JSON subtitle dict.
    Mirrors zMovieTextInjector.genSubBlock.

    Each entry: 4-byte little-endian length field + subtitle bytes.
    The block ends with a duplicate of the last subtitle (null length prefix).
    """
    encoded_subs = []
    for startFrame in sorted(subtitlesJson.keys(), key=int):
        entry = subtitlesJson[startFrame]
        sb = _encodeSubtitle(
            int(startFrame),
            int(entry.get("duration", "0")),
            entry.get("text", "")
        )
        encoded_subs.append(sb)

    block = b''
    for sb in encoded_subs:
        length = struct.pack("I", len(sb) + 4)
        block += length + sb

    # Duplicate final entry with null length prefix (matches original format)
    if encoded_subs:
        block += bytes(4) + encoded_subs[-1]

    return block


def _rebuildEntry(origSlice: bytes, subtitlesJson: dict) -> bytes:
    """
    Reconstruct one zmovie entry binary with patched subtitle data.

    Layout (from zMovieTextInjector.py):
      origSlice[:0x38]     — static header (unchanged)
      genSubBlock(...)     — new subtitle bytes
      padding to 0x800     — zero-fill
      origSlice[0x800:]    — original video/audio data (unchanged)
    """
    sub_block = _buildSubBlock(subtitlesJson)
    header    = origSlice[:0x38]
    subtitle_section = header + sub_block

    if len(subtitle_section) > SUBTITLE_PATCH_LIMIT:
        raise ValueError(
            f"Subtitle block is {len(subtitle_section)} bytes — exceeds "
            f"0x{SUBTITLE_PATCH_LIMIT:X} limit by "
            f"{len(subtitle_section) - SUBTITLE_PATCH_LIMIT} bytes. "
            "Shorten subtitle text."
        )

    subtitle_section += bytes(SUBTITLE_PATCH_LIMIT - len(subtitle_section))
    return subtitle_section + origSlice[SUBTITLE_PATCH_LIMIT:]


def compileToFile(outputPath: str, originalData: bytes, dialogueJson: dict) -> None:
    """
    Patch zmovie subtitle data and write a new ZMOVIE.STR.

    Parameters
    ----------
    outputPath : str
    originalData : bytes   — original ZMOVIE.STR bytes (used for TOC + video data)
    dialogueJson : dict    — {"zmovie-00": {"startFrame": {"duration": ..., "text": ...}}}
    """
    offsets = getEntryOffsets(originalData)
    offsets.append(len(originalData))

    # TOC block is kept verbatim
    output = bytearray(originalData[:ZMOVIE_BLOCK])

    for i in range(len(offsets) - 1):
        start, end = offsets[i], offsets[i + 1]
        orig_slice = originalData[start:end]
        key = f"zmovie-{i:02}"
        if key in dialogueJson:
            new_slice = _rebuildEntry(orig_slice, dialogueJson[key])
        else:
            new_slice = orig_slice
        output.extend(new_slice)

    with open(outputPath, 'wb') as f:
        f.write(bytes(output))
    print(f"ZMOVIE.STR written to: {outputPath}")


# ── Video extraction ─────────────────────────────────────────────────────────

def extractEntryVideo(originalData: bytes, entryIndex: int, outputPath: str) -> None:
    """
    Extract video+audio from a single zmovie entry as a standard PSX STR file.

    Each 0x920-byte block in ZMOVIE.STR has an 8-byte CD-XA subheader followed
    by 2328 bytes of payload. This reconstructs standard 2352-byte raw CD
    sectors (sync + header + subheader + payload) that ffmpeg can decode.

    Block 0 of each entry is the subtitle header and is skipped.

    Parameters
    ----------
    originalData : bytes    — full ZMOVIE.STR file bytes
    entryIndex   : int      — 0-3
    outputPath   : str      — path to write the .str file
    """
    offsets = getEntryOffsets(originalData)
    offsets.append(len(originalData))

    start = offsets[entryIndex]
    end = offsets[entryIndex + 1]
    num_blocks = (end - start) // ZMOVIE_BLOCK

    with open(outputPath, 'wb') as out:
        for blk in range(1, num_blocks):  # skip block 0 (subtitle header)
            off = start + blk * ZMOVIE_BLOCK
            subheader = originalData[off:off + _XA_SUBHEADER_SIZE]
            payload = originalData[off + _XA_SUBHEADER_SIZE:off + ZMOVIE_BLOCK]

            # Fake CD header: minute, second, sector, mode=2
            cd_header = bytes([0, 0, blk % 75, 2])
            raw_sector = _CD_SYNC + cd_header + subheader + payload
            # Pad to standard 2352-byte sector
            out.write(raw_sector.ljust(_RAW_SECTOR_SIZE, b'\x00'))
