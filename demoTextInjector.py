"""
Adapted from Green Goblins scripts. 
This is really heavily based on his awesome work. 

# Script for working with Metal Gear Solid data
#
# Copyright (C) 2023 Green_goblin (https://mgsvm.blogspot.com/)
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.

"""

import os
import re
import glob
import struct
import progressbar
from radioTools import radioDict as RD
import json

import demoTextExtractor as DTE

version = "usa"
version = "jpn"

# Toggles
debug = True


# Directory configs
inputDir = f'demoWorkingDir/{version}/bins'
outputDir = f'demoWorkingDir/{version}/newBins'
injectJson = f'demoWorkingDir/{version}/demoText-{version}.json'
os.makedirs(outputDir, exist_ok=True)

bin_files = glob.glob(os.path.join(inputDir, '*.bin'))
bin_files.sort(key=lambda f: int(f.split('-')[1].split('.')[0]))

injectTexts = json.load(open(injectJson, 'r'))

skipFilesListD1 = [
    'demo-5',
    'demo-6',
    'demo-31',
    'demo-33',
    'demo-35',
    'demo-63',
    'demo-67',
    'demo-71',
    'demo-72',
]

def injectSubtitles(originalBinary: bytes, newTexts: dict, startingNum: int = 1) -> tuple [bytes, int]:
    """
    Injects the new text to the original data, returns the bytes. 
    Also returns the index we were at when we finished. 
    """ 

    def encodeNewText(text: str):
        """
        Simple. Encodes the text as bytes. 
        Adds the buffer we need to be divisible by 4...
        Return the new bytes.
        """
        newBytes: bytes = RD.encodeJapaneseHex(text)[0]
        bufferNeeded = 4 - (len(newBytes) % 4)
        for j in range(bufferNeeded):
            newBytes += b'\x00'
            j += 1
        
        return newBytes
    
    newBytes = b""
    firstLengthBytes = originalBinary[18:20]
    firstLength = struct.unpack('<H', firstLengthBytes)[0]
    offset = 8 + firstLength # This is our starting point for the dialogue.

    newBytes += originalBinary[0: offset]

    i = startingNum
    while i <= len(newTexts):
        if originalBinary[offset] == 0x00:
            # Find the length here (This is stupid!)
            origTextData = originalBinary[offset: offset + originalBinary.find(b'\x00', offset + 16)] # We can add the buffer later
            bufferNeeded = 4 - (len(origTextData) % 4)
            origTextLength = len(origTextData) + bufferNeeded
            origTextData = originalBinary[offset: offset + origTextLength]

            # Now create the new one.
            newText = encodeNewText(newTexts[str(i)])
            newBytes = newBytes + origTextData[0:16] + newText
            i += 1
            offset += origTextLength
            break
        else:
            origLength = originalBinary[offset]
            origTextData = originalBinary[offset: offset + origLength]
            origTextLength = len(origTextData)
            # New Text
            newText = encodeNewText(newTexts[str(i)])
            newLength = len(newText) + 16
            newBytes += newLength.to_bytes() + origTextData[1:16] + newText
        
            i += 1
            offset += origTextLength

    return newBytes, i  


    
if debug:
    print(f'Only injecting Demo 25!')
    # bin_files = ['demoWorkingDir/usa/bins/demo-25.bin']

for file in bin_files:
    print(os.path.basename(file))
    filename = os.path.basename(file)
    basename = filename.split(".")[0]

    if debug:
        print(f'Processing {basename}')

    if basename in skipFilesListD1:
        if debug:
            print(f'{basename} in skip list. Continuing...')
        continue

    # if injectTexts[basename] is None:
    if basename not in injectTexts:
        print(f'{basename} was not in the json. Skipping...')
        continue
    
    # Initialize the demo data and the dictionary we're using to replace it.
    origDemoData = open(file, 'rb').read()
    demoDict: dict = injectTexts[basename]

    offsets = DTE.getTextAreaOffsets(origDemoData)
    nextStart = 1
    newDemoData = origDemoData[0 : offsets[0]]

    for Num in range(len(offsets)):
        subset = DTE.getTextAreaBytes(offsets[Num], origDemoData)
        newData, nextStart = injectSubtitles(subset, demoDict, nextStart)
        newDemoData += newData 
        if Num < len(offsets) - 1:
            newDemoData += origDemoData[len(newDemoData): offsets[Num + 1]]
        else:
            newDemoData += origDemoData[len(newDemoData): ]
        print(newData.hex())

    newFile = open(f'{outputDir}/{basename}.bin', 'wb')
    newFile.write(newDemoData)
    newFile.close()
    # print(demoDict)




"""
# not really needed just for reference.
for key in injectTexts:
    print(key)
    demoDict: dict = injectTexts[key]
    
"""