"""
Adjust VOX.DAT offsets in STAGE.DIR and RADIO.DAT XML after VOX files have been reinjected.

STAGE.DIR: VOX references use the GCL "Pv" tag (50 76), storing block indices
(byte_offset / 0x800) as 4-byte big-endian integers prefixed by 0x0a type markers.
  Single:  50 76 06 0a [4B BE block index]
  Multi:   50 76 [payload_size] 0a [4B] 0a [4B] ...

RADIO XML: VOX_CUES elements have a "voxCode" attribute containing the block index
as an 8-char hex string (e.g. "00014bc7"). A voxCode of "00000000" means the voice
line is on the other disc and must be left alone.

Usage:
  python3 voxOffsetAdjuster.py -o old.json -n new.json -s STAGE.DIR [--radio RADIO.xml] [-v] [-f]

Offset json files map vox number (e.g. "0001") to raw byte offset hex string (e.g. "00003800").
Block index = raw_offset / 0x800.
"""

import struct, json
import os, sys, argparse
import xml.etree.ElementTree as ET
from progressbar import ProgressBar

bar = ProgressBar()

debug = False

def importOffsets(filename: str) -> dict:
    with open(filename, "r") as f:
        offsets: dict = json.load(f)
    return offsets

def buildBlockMap(origOffsets: dict, newOffsets: dict) -> dict:
    """
    Build a mapping of {old_block_index: new_block_index} from raw byte offset hex strings.
    """
    blockMap = {}
    for key in origOffsets.keys():
        oldRaw = int(origOffsets[key], 16)
        newRaw = int(newOffsets[key], 16)
        oldBlock = oldRaw // 0x800
        newBlock = newRaw // 0x800
        blockMap[oldBlock] = newBlock
    return blockMap

def adjustVoxOffsets(stageData: bytearray, blockMap: dict) -> int:
    """
    Scan STAGE.DIR for Pv tags (50 76) and replace old block indices with new ones.
    Returns the number of replacements made.
    """
    global debug
    patternPv = bytes.fromhex("5076")
    offset = 0
    replacements = 0
    skipped = 0

    bar.maxval = len(stageData)
    bar.start()

    while offset < len(stageData) - 2:
        if stageData[offset:offset + 2] == patternPv:
            payloadSize = stageData[offset + 2]

            # Parse all 0a-prefixed 4-byte values within the payload
            pos = offset + 3  # Start of payload
            payloadEnd = offset + 3 + payloadSize
            if payloadEnd > len(stageData):
                offset += 1
                bar.update(offset)
                continue

            while pos < payloadEnd:
                if stageData[pos] == 0x0a and pos + 5 <= payloadEnd:
                    oldBlock = struct.unpack('>I', stageData[pos + 1: pos + 5])[0]

                    if oldBlock == 0xFFFFFFFF:
                        if debug:
                            print(f'  0x{offset:06X}: FFFFFFFF sentinel, skipping')
                        pos += 5
                        continue

                    if oldBlock in blockMap:
                        newBlock = blockMap[oldBlock]
                        if oldBlock != newBlock:
                            stageData[pos + 1: pos + 5] = struct.pack('>I', newBlock)
                            replacements += 1
                            if debug:
                                print(f'  0x{offset:06X}: Replaced block {oldBlock} (0x{oldBlock:04X}) -> {newBlock} (0x{newBlock:04X})')
                        else:
                            skipped += 1
                    else:
                        if debug:
                            print(f'  0x{offset:06X}: Block {oldBlock} (0x{oldBlock:04X}) not in offset map!')
                    pos += 5
                else:
                    pos += 1  # Skip unexpected bytes within payload

            offset = payloadEnd
        else:
            offset += 1
        bar.update(min(offset, len(stageData)))

    bar.finish()
    if debug:
        print(f'  Unchanged: {skipped}')
    return replacements

def adjustRadioXml(xmlPath: str, blockMap: dict) -> int:
    """
    Patch voxCode attributes in VOX_CUES elements of a RADIO XML file.
    voxCode "00000000" means the voice line is on the other disc — skip it.
    Returns the number of replacements made.
    """
    global debug
    tree = ET.parse(xmlPath)
    root = tree.getroot()
    replacements = 0
    skipped = 0

    for voxElem in root.iter('VOX_CUES'):
        voxCode = voxElem.get('voxCode')
        if voxCode is None:
            continue

        oldBlock = int(voxCode, 16)

        # Null voxCode = other disc, leave it alone
        if oldBlock == 0:
            if debug:
                print(f'  voxCode 00000000 (other disc), skipping')
            skipped += 1
            continue

        if oldBlock in blockMap:
            newBlock = blockMap[oldBlock]
            if oldBlock != newBlock:
                voxElem.set('voxCode', f'{newBlock:08x}')
                replacements += 1
                if debug:
                    print(f'  voxCode {voxCode} -> {newBlock:08x}')
            else:
                skipped += 1
        else:
            if debug:
                print(f'  voxCode {voxCode} (block {oldBlock}) not in offset map!')

    if replacements > 0:
        tree.write(xmlPath, encoding='unicode', xml_declaration=True)

    if debug:
        print(f'  Unchanged: {skipped}')
    return replacements

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adjust VOX.DAT offsets in STAGE.DIR")
    parser.add_argument("-o", "--old-offsets", required=True, type=str, help="Original VOX offsets JSON file")
    parser.add_argument("-n", "--new-offsets", required=True, type=str, help="New VOX offsets JSON file")
    parser.add_argument("-s", "--stage", required=True, type=str, help="STAGE.DIR file to modify")
    parser.add_argument("-O", "--output", type=str, help="Output STAGE.DIR path (default: overwrites input)")
    parser.add_argument("-r", "--radio", type=str, help="Radio XML file to patch voxCode attributes in")
    parser.add_argument("-v", "--debug", action="store_true", help="Verbose debug output")
    parser.add_argument("-f", "--force", action="store_true", help="Skip interactive confirmation")
    args = parser.parse_args()

    debug = args.debug
    outputFile = args.output if args.output else args.stage

    if not args.force and outputFile == args.stage:
        confirm = input(
            "WARNING: This will overwrite the STAGE.DIR file in place!\n"
            f"File: {args.stage}\n"
            "Type \"CONFIRM\" to continue!\n> "
        )
        if confirm != "CONFIRM":
            print("Aborted.")
            exit(0)

    origOffsets = importOffsets(args.old_offsets)
    newOffsets = importOffsets(args.new_offsets)
    blockMap = buildBlockMap(origOffsets, newOffsets)

    changedBlocks = sum(1 for k, v in blockMap.items() if k != v)
    print(f'Loaded {len(blockMap)} VOX offsets ({changedBlocks} changed)')

    if changedBlocks == 0:
        print("No offsets changed. Nothing to do!")
        exit(0)

    stageData = bytearray(open(args.stage, "rb").read())
    print(f"Adjusting STAGE.DIR VOX offsets (Pv tags)...")
    replacements = adjustVoxOffsets(stageData, blockMap)

    print(f"Replaced {replacements} VOX block references in STAGE.DIR")

    with open(outputFile, 'wb') as out:
        out.write(stageData)
        print(f'Written: {outputFile}')

    # Patch radio XML if provided
    if args.radio:
        print(f"Adjusting Radio XML voxCode attributes...")
        radioReplacements = adjustRadioXml(args.radio, blockMap)
        print(f"Replaced {radioReplacements} voxCode references in {args.radio}")

    exit(0)
