"""
Compares two binary files and reports back the offset where the file breaks
"""

import os, struct
import radioDict 
import argparse


parser = argparse.ArgumentParser("Compare two binary files and figure out where they differ")

parser.add_argument('input', type=str, help="Input Filename from script (.bin).")
parser.add_argument('output', type=str, help="Output Filename from script (.bin).")

originalFile = open(args.input, 'rb')
originalData = originalFile.read()

compareFile = open(args.output, 'rb')
compareData = compareFile.read()

print(f'Original file: {len(originalData)} bytes. New file: {len(compareData)} bytes')

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
        print(f"Files break at offset c.")
        print(f'Offset in hex: {struct.pack('>H', offset)}')
    
