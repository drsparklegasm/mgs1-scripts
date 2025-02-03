"""
I don't remember who wrote this. Looks like mine but could've been Goblin. 
Either way... modified.

# Script for working with Metal Gear Solid data
#
# Copyright (C) 2023 Green_goblin (https://mgsvm.blogspot.com/)
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
"""

import os

version = 'usa'
# version = 'jpn'

filename = f"demoWorkingDir/originalDats/DEMO-{version}-d1.DAT"
outputDir = f"demoWorkingDir/{version}/bins"
os.makedirs(f'demoWorkingDir/{version}/bins', exist_ok=True)

demoFile = open(filename, 'rb')
demoData = demoFile.read()

opening = b'\x10\x08\x00\x00'  # Adjusted opening pattern

offsets = []
def findDemoOffsets():
    offset = 0
    while offset < len(demoData) - 4:  # Adjusted for the new opening length
        checkbytes = demoData[offset:offset + 4]  # Check the first 4 bytes
        if checkbytes == opening:
            print(f'Offset found at offset {offset}!')
            offsets.append(offset)
            offset += 2048  # Continue using 2048 as the increment step for speed
        else:
            offset += 2048

    print(f'Ending! {len(offsets)} offsets found:')
    for offset in offsets:
        print(offset.to_bytes(4, 'big').hex())

def splitDemoFiles():
    for i in range(len(offsets)):  
        start = offsets[i] 
        if i < len(offsets) - 1:
            end = offsets[i + 1]
        else:
            end = len(demoData)  # Include the last byte
        f = open(f'{outputDir}/demo-{i + 1:02}.bin', 'wb')
        f.write(demoData[start:end])
        f.close()
        print(f'Demo {i + 1} written!')
    
    print(f'{i+1} demo files written!')

if __name__ == '__main__':
    findDemoOffsets()
    splitDemoFiles()
