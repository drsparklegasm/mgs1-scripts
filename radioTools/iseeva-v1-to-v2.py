"""
Takes a reference Iseeeva JSON (with the vox layer) to determine which
subtitle offsets belong under which VOX_CUES offset. Subtitle text comes
from the v1 file — the reference only provides the structure.

Usage:
    python myScripts/radioTools/iseeeva-v1-to-v2.py <old.json> <reference-Iseeva.json> [output.json]

If output is omitted, writes to RADIO-Iseeeva-upgraded.json next to the input.
"""

import sys, os
sys.path.append(os.path.abspath('./myScripts'))

import json
import argparse

parser = argparse.ArgumentParser(
    description='Upgrade flat RADIO-Iseeeva.json to VOX-layered format using a reference Iseeeva JSON.')
parser.add_argument('input', type=str, help='Flat RADIO-Iseeeva.json to upgrade')
parser.add_argument('reference', type=str, help='New-format Iseeeva JSON with VOX layer (e.g. RADIO-Iseeva.json)')
parser.add_argument('output', nargs='?', type=str, help='Output filename (default: RADIO-Iseeeva-upgraded.json)')

def main(args=None):
    if args is None:
        args = parser.parse_args()

    with open(args.input, 'r', encoding='utf8') as f:
        original = json.load(f)

    with open(args.reference, 'r', encoding='utf8') as f:
        reference = json.load(f)

    refCalls = reference['calls']
    upgraded = {}
    unmatched_total = 0

    for callOffset, flatSubs in original.items():
        if callOffset not in refCalls:
            # Call not in reference — wrap all subs under "none"
            upgraded[callOffset] = {"none": flatSubs}
            print(f'Warning: call {callOffset} not found in reference, placed under "none"')
            continue

        refVoxDict = refCalls[callOffset]
        # Build a reverse lookup: sub_offset → vox_offset from the reference
        subToVox = {}
        for voxOffset, refSubs in refVoxDict.items():
            for subOffset in refSubs.keys():
                subToVox[subOffset] = voxOffset

        # Distribute story subs into their VOX buckets
        newCallVox = {}
        unmatched = {}
        for subOffset, text in flatSubs.items():
            voxOffset = subToVox.get(subOffset)
            if voxOffset is not None:
                newCallVox.setdefault(voxOffset, {})[subOffset] = text
            else:
                unmatched[subOffset] = text

        if unmatched:
            newCallVox["none"] = unmatched
            unmatched_total += len(unmatched)
            print(f'Warning: call {callOffset} has {len(unmatched)} sub(s) not matched to any VOX')

        upgraded[callOffset] = newCallVox

    # Write output
    outputFile = args.output
    if not outputFile:
        base, ext = os.path.splitext(args.input)
        outputFile = f'{base}-upgraded{ext}'

    with open(outputFile, 'w', encoding='utf8') as f:
        json.dump(upgraded, f, ensure_ascii=False, indent=2)

    print(f'Upgraded {len(upgraded)} calls → {outputFile}')
    if unmatched_total:
        print(f'{unmatched_total} subtitle(s) could not be matched to a VOX offset')

if __name__ == '__main__':
    main()
