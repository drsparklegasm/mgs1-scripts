"""
Extract dialogue and timing data from DEMO.DAT or VOX.DAT directly,
without pre-splitting into individual .dmo/.vox files.

Output JSON format matches v2 from demoTextExtractor.py:
  { "demo-01": { "1234": { "duration": "5678", "text": "..." } }, ... }

Usage (CLI):
    python DemoTools/extractDemoVox.py DEMO.DAT [output.json]
    python DemoTools/extractDemoVox.py VOX.DAT [output.json] --type vox

Usage (module):
    from DemoTools.extractDemoVox import extractFromFile
    data = extractFromFile("DEMO.DAT")
"""

import os, sys, json, argparse

# Allow imports from the parent scripts/ directory
_here = os.path.dirname(os.path.abspath(__file__))
_scripts = os.path.dirname(_here)
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

import demoClasses as demoCtrl

DEMO_HEADER = b'\x10\x08\x00\x00'
CHUNK_SIZE = 0x800


def findOffsets(data: bytes) -> list:
    """
    Scan data in 0x800-byte steps and collect offsets that begin with the
    standard demo/vox file header.  This is the same strategy used by
    demoSplitter.py and voxSplit.py, but operates entirely in-memory.
    """
    offsets = []
    offset = 0
    while offset < len(data) - 4:
        if data[offset:offset + 4] == DEMO_HEADER:
            offsets.append(offset)
        offset += CHUNK_SIZE
    return offsets


def extractSubtitles(entryData: bytes) -> dict:
    """
    Parse one demo/vox binary blob and return all subtitle data.

    Returns a dict mapping startFrame (str) → {"duration": str, "text": str}.
    Returns an empty dict if the entry contains no caption chunks.
    """
    try:
        items = demoCtrl.parseDemoData(entryData)
    except Exception as e:
        print(f"  Warning: parse error — {e}")
        return {}

    result = {}
    for item in items:
        if isinstance(item, demoCtrl.captionChunk):
            for sub in item.subtitles:
                text = sub.text.replace('\x00', '')
                result[str(sub.startFrame)] = {
                    "duration": str(sub.displayFrames),
                    "text": text,
                }
    return result


def extractFromFile(inputPath: str, fileType: str = None) -> dict:
    """
    Extract all subtitle data from a DEMO.DAT or VOX.DAT file without
    writing any intermediate split files.

    Parameters
    ----------
    inputPath : str
        Path to DEMO.DAT or VOX.DAT.
    fileType : str, optional
        "demo" or "vox".  Auto-detected from the filename if omitted.

    Returns
    -------
    dict
        Keyed by entry name ("demo-01" / "vox-0001").
        Only entries that contain dialogue are included.
    """
    basename = os.path.basename(inputPath).upper()
    if fileType is None:
        fileType = "vox" if "VOX" in basename else "demo"

    with open(inputPath, 'rb') as f:
        data = f.read()

    offsets = findOffsets(data)
    print(f"  Found {len(offsets)} {fileType} entries in {os.path.basename(inputPath)}.")

    result = {}
    for i, start in enumerate(offsets):
        end = offsets[i + 1] if i + 1 < len(offsets) else len(data)
        entryData = data[start:end]

        key = f"demo-{i + 1:02}" if fileType == "demo" else f"vox-{i + 1:04}"
        subtitles = extractSubtitles(entryData)
        if subtitles:
            result[key] = subtitles

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Extract dialogue/timings from DEMO.DAT or VOX.DAT to JSON.'
    )
    parser.add_argument('input', type=str,
                        help='Input DEMO.DAT or VOX.DAT file.')
    parser.add_argument('output', type=str, nargs='?', default=None,
                        help='Output JSON path. Defaults to <input-stem>-dialogue.json.')
    parser.add_argument('--type', choices=['demo', 'vox'], default=None,
                        help='Force file type (auto-detected from filename if omitted).')
    args = parser.parse_args()

    outputPath = args.output
    if outputPath is None:
        stem = os.path.splitext(os.path.basename(args.input))[0].lower()
        outputPath = f"{stem}-dialogue.json"

    print(f"Extracting from: {args.input}")
    data = extractFromFile(args.input, args.type)
    print(f"Entries with dialogue: {len(data)}")

    with open(outputPath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Written to: {outputPath}")


if __name__ == '__main__':
    main()
