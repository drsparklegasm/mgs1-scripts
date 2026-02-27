"""
Pretty much follows the same rules as demo.dat for chunking

"""

import os
import argparse

parser = argparse.ArgumentParser(description='Split VOX.DAT into individual .vox files')
parser.add_argument('filename', type=str, help='Input VOX.DAT file to split.')
parser.add_argument('output', nargs='?', type=str, help='Output directory for .vox files.')
parser.add_argument('-v', '--verbose', action='store_true', help='Show debug output.')

# Globals
demoData = b''
offsets = []
outputDir = ''
debug = False
opening = b'\x10\x08\x00\x00'  # Adjusted opening pattern

def findDemoOffsets():
    offset = 0
    while offset < len(demoData) - 4:  # Adjusted for the new opening length
        checkbytes = demoData[offset:offset + 4]  # Check the first 4 bytes
        if checkbytes == opening:
            offsets.append(offset)
            offset += 2048  # Continue using 2048 or 0x800 as the increment step for speed
        else:
            offset += 2048

def splitDemoFiles():
    for i in range(len(offsets)):
        start = offsets[i]
        if i < len(offsets) - 1:
            end = offsets[i + 1]
        else:
            end = len(demoData)  # Include the last byte
        f = open(f'{outputDir}/vox-{i + 1:04}.vox', 'wb')
        f.write(demoData[start:end])
        f.close()
        if debug:
            print(f'Wrote VOX file {i}')

def main(args=None):
    global filename, outputDir, debug, demoData, offsets

    if args is None:
        args = parser.parse_args()

    filename = args.filename
    outputDir = args.output if args.output else os.path.join(os.path.dirname(os.path.abspath(filename)), 'bins')
    debug = args.verbose

    with open(filename, 'rb') as f:
        demoData = f.read()

    os.makedirs(outputDir, exist_ok=True)

    findDemoOffsets()
    if debug:
        for offset in offsets:
            print(f"{offset}: {hex(offset)} / Block {offset // 2048}")
    splitDemoFiles()

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)