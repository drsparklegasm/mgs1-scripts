"""
Compares two binary files and reports back the offset where the file breaks
"""

import os, struct
# import translation.radioDict as radioDict 
import argparse

# Start by parsing old and new files

parser = argparse.ArgumentParser("Compare two binary files and figure out where they differ")

parser.add_argument('input', type=str, help="Input Filename from script (.bin).")
parser.add_argument('output', type=str, help="Output Filename from script (.bin).")
parser.add_argument('-a','--allDiffs', action='store_true', help="Prints all errors (as opposed to breaking at the first one)")

args = parser.parse_args()

##########################################
if args.output:
    originalFile = open(args.input, 'rb')
    originalData = originalFile.read()
else:
    originalFile = open(f'extractedCallBins/{args.input}.bin', 'rb')
    originalData = originalFile.read()

if args.output:
    compareFile = open(args.output, 'rb')
    compareData = compareFile.read()
else:
    compareFile = open(f'recompiledCallBins/{args.input}-mod.bin', 'rb')
    compareData = compareFile.read()

print(f'Original file: {len(originalData)} bytes. New file: {len(compareData)} bytes')

# Main comparison loop
offset = 0

if len(originalData) > len(compareData):
    size = len(originalData)
    print("Original Data is larger!")
elif len(compareData) > len(originalData):
    size = len(compareData)
    print("New Data is larger!")
else:
    print("The files are equal size!")
    size = len(compareData)

while offset < size:
    if originalData[offset] == compareData[offset]:
        offset += 4
    elif originalData[offset : offset + 2] == bytes.fromhex("9016") and compareData[offset : offset + 2] == bytes.fromhex("d016"):
        print(f'Character mismatch! {originalData[offset : offset + 2]} {compareData[offset : offset + 2]} ')
        offset += 2
    else:
        differ = True
        print(f"Files break at offset {offset}")
        offsetHex = struct.pack('>L', offset)
        print(f'Offset in hex: 0x{offsetHex.hex()}')
        print(f'Original: \n{originalData[offset - 10 : offset + 10].hex()}')
        print(f'New Data: \n{compareData[offset - 10 : offset + 10].hex()}')
        offset += 1
        if not args.allDiffs:
            break
    print(f"Checking offset = {offset}\r")


