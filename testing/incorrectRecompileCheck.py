"""
Compares two binary files and reports back the offset where the file breaks
"""

import os, struct
# import radioTools.radioDict as radioDict 
import argparse

# Start by parsing old and new files

parser = argparse.ArgumentParser("Compare two binary files and figure out where they differ")

parser.add_argument('input', type=str, help="Input Filename from script (.bin).")
# parser.add_argument('output', type=str, help="Output Filename from script (.bin).")

args = parser.parse_args()

##########################################

originalFile = open(f'extractedCallBins/{args.input}.bin', 'rb')
originalData = originalFile.read()

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

while offset < size:
    if originalData[offset] == compareData[offset]:
        offset += 1
    else:
        differ = True
        print(f"Files break at offset {offset}.")
        offsetHex = struct.pack('>H', offset)
        print(f'Offset in hex: 0x{offsetHex.hex()}')
        break

if differ:
    print(f'Original: \n{originalData[offset - 10 : offset + 10].hex()}')
    print(f'New Data: \n{compareData[offset - 10 : offset + 10].hex()}')
    
