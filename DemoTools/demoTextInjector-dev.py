"""
Adapted from Green Goblins scripts. 
This is really heavily based on his awesome work. 

Script for working with Metal Gear Solid data

Copyright (C) 2023 Green_goblin (https://mgsvm.blogspot.com/)

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

"""

import os, sys
sys.path.append(os.path.abspath('./myScripts'))
import re
import glob
import struct
import progressbar
import radioTools.radioDict as RD
import json

import DemoTools.demoTextExtractor as DTE

version = "usa"
# version = "jpn"

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

class subtitle:
    text: str
    startFrame: int
    duration: int

    def __init__(self, dialogue, b, c) -> None:
        self.text = dialogue
        self.startFrame = b
        self.duration = c

        return
    
    def __str__(self) -> str:
        a = f'Subtitle contents: Start: {self.startFrame} Duration: {self.duration} Text: {self.text}'
        return a
    
    def __bytes__(self) -> bytes:
        """
        Simple. Encodes the dialogue as bytes. 
        Adds the buffer we need to be divisible by 4...
        Return the new bytes.
        """
        subtitleBytes: bytes = struct.pack("III", self.start, self.duration, 0)
        subtitleBytes += RD.encodeJapaneseHex(self.text)[0]
        bufferNeeded = 4 - (len(subtitleBytes) % 4)
        subtitleBytes += bytes(bufferNeeded)
        
        return subtitleBytes

def assembleTitles(texts: dict, timings: dict) -> list [subtitle]:
    subsList = []
    for i in range(len(texts)):
        start = timings.get(i).split(",")[0]
        duration = timings.get(i).split(",")[1]
        a = subtitle(texts.get(i), start, duration)
        subsList.append(a)
    
    return subsList
"""
# TODO:
- change key to int
- make sure range hits all texts
"""
skipFilesListD1 = [
    'demo-05',
    'demo-06',
    'demo-31',
    'demo-33',
    'demo-35',
    'demo-63',
    'demo-67',
    'demo-71',
    'demo-72',
]

def genSubBlock(newTexts: dict, frameLimit: int = 1, timings: dict = None) -> bytes:
    """
    Injects the new text to the original data, returns the bytes. 
    Also returns the index we were at when we finished. 

    """ 
    
    
    pass

def injectSubtitles(originalBinary: bytes, newTexts: dict, frameLimit: int = 1, timings: dict = None) -> bytes:
    """
    Injects the new text to the original data, returns the bytes. 
    Also returns the index we were at when we finished. 

    New vers: Framelimit is the end of a cutscene segment.
    """ 

    def encodeNewText(text: str, timing: str):
        """
        Simple. Encodes the dialogue as bytes. 
        Adds the buffer we need to be divisible by 4...
        Return the new bytes.
        """
        timings = int(timing.split(','))
        start = timings[0]
        duration = timings[1]

        subtitleBytes: bytes = struct.pack("III", start, duration, 0)
        subtitleBytes += RD.encodeJapaneseHex(text)[0]
        bufferNeeded = 4 - (len(subtitleBytes) % 4)
        for j in range(bufferNeeded):
            newBytes += b'\x00'
            j += 1
        
        return subtitleBytes
    

    
    newBytes = b""
    firstLengthBytes = originalBinary[18:20]
    firstLength = struct.unpack('<H', firstLengthBytes)[0]
    offset = 8 + firstLength # This is our starting point for the dialogue.

    newBytes += originalBinary[0: offset]

    # i = startingNum
    while i <= len(newTexts):
        start, duration = timings.get(f"{i}").split(",")
        start = int(start)
        duration = int(duration)
        if originalBinary[offset] == 0x00:
            # Find the length here (This is stupid!)
            origTextData = originalBinary[offset: offset + originalBinary.find(b'\x00', offset + 16)] # We can add the buffer later
            bufferNeeded = 4 - (len(origTextData) % 4)
            origTextLength = len(origTextData) + bufferNeeded
            origTextData = originalBinary[offset: offset + origTextLength]

            # Now create the new one.
            newText = encodeNewText(newTexts[str(i)])
            newBytes = newBytes + origTextData[0:4] + struct.pack("<I", start) + struct.pack("<I", duration) + origTextData[12:16] + newText
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
            newBytes += newLength.to_bytes() + origTextData[1:4] + struct.pack("<I", start) + struct.pack("<I", duration) + origTextData[12:16] + newText
        
            i += 1
            offset += origTextLength

    return newBytes

if debug:
    print(f'Only injecting Demo 25!')
    # bin_files = ['demoWorkingDir/usa/bins/demo-25.bin']

if __name__ == "__main__":
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
        origBlocks = len(origDemoData) // 0x800
        demoDict: dict = injectTexts[basename][0]
        timings: dict = injectTexts[basename][1]

        offsets = DTE.getTextAreaOffsets(origDemoData)
        # nextStart = 1 # index of subtitle to encode. No longer needed.
        newDemoData = origDemoData[0 : offsets[0]] # BEFORE the header

        newSubsData = b''
        for Num in range(len(offsets)):
            subset = DTE.getTextAreaBytes(offsets[Num], origDemoData)
            limitFrame = struct.unpack("<I", subset[])
            newData = injectSubtitles(subset, demoDict, limitFrame, timings)
            """
            TODO! Write new header here.
            """
            newSubsData += newData 
            if Num < len(offsets) - 1:
                newSubsData += origDemoData[len(newSubsData): offsets[Num + 1]]
            else:
                newSubsData += origDemoData[len(newSubsData): ]
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