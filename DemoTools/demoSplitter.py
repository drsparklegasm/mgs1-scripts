import os, struct
import argparse
# import progressbar, time

"""
This file has been heavily modified to accept arguments, and split both DEMO.DAT and VOX.DAT as they share formatting/chunking. 
"""

parser = argparse.ArgumentParser(description=f'Split DEMO/VOX files into individual files')

# REQUIRED
parser.add_argument('filename', type=str, help="DEMO.DAT or VOX.DAT file to split.")
parser.add_argument('output', nargs="?", type=str, help="Output path")

# Legacy
version = "jpn"
disc = 2
filename = f"build-src/{version}-d{disc}/MGS/DEMO.DAT"
outputDir = f"workingFiles/{version}-d{disc}/demo/bins"
demoData: bytes

# Output modifier
extension = ".bin" # overwritten if we know whether it's DEMO or VOX

def initRadioData():
    global filename
    global demoData

    demoFile = open(filename, 'rb')
    demoData = demoFile.read()
    return

offsets = []
opening = b'\x10\x08\x00\x00'
# opening = b'\x10\x08\x00\x00\x05\x00\x00\x00'

def findDemoOffsets():
    global extension
    offset = 0
    while offset < len(demoData) - 8:
        # print(f'We\'re at {offset}\n')
        checkbytes = demoData[offset:offset + 4]
        if checkbytes == opening:
            print(f'Offset found at offset {offset}!')
            offsets.append(offset)
            offset += 2048 # All demo files are aligned to 0x800, SIGNIFICANTLY faster to do this than +8! Credit to Green Goblin
        else:
            offset += 2048

    print(f'Ending! {len(offsets)} offsets found:')
    for offset in offsets:
        print(offset.to_bytes(4, 'big').hex())

def splitDemoFiles():
    global extension
    i = 0
    offsetFile = open(f'{outputDir}/{extension}Offsets.txt', 'w')
    for i in range(len(offsets)):  
        start = offsets[i] 
        if i < len(offsets) - 1:
            end = offsets[i + 1]
        else:
            end = len(demoData) 
        f = open(f'{outputDir}/{extension}-{i + 1:02}.{extension}', 'wb')
        offsetFile.write(f'{i + 1:02}: {start:08x} - {end:08x}, length: {end - start}\n')
        f.write(demoData[start:end])
        f.close()
        print(f'File {extension} {i + 1} written!')
    
    print(f'{len(offsets)} {extension} files written!')

def main(args=None):
    global filename
    global outputDir
    global extension

    if args is None:
        args = parser.parse_args()

    filename = args.filename
    outputDir = args.output

    if "VOX" in filename:
        extension = "vox"
    elif "DEMO" in filename:
        extension = "dmo"

    os.makedirs(outputDir, exist_ok=True)
    initRadioData()

    findDemoOffsets()
    splitDemoFiles()

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)