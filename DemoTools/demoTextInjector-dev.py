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
        self.startFrame = int(b)
        self.duration = int(c)

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
        subtitleBytes: bytes = struct.pack("III", self.startFrame, self.duration, 0)
        subtitleBytes += RD.encodeJapaneseHex(self.text)[0]
        bufferNeeded = 4 - (len(subtitleBytes) % 4)
        subtitleBytes += bytes(bufferNeeded)
        
        return subtitleBytes

def assembleTitles(texts: dict, timings: dict) -> list [subtitle]:
    subsList = []
    for i in range(len(texts)):
        start = timings.get(str(i + 1)).split(",")[0]
        duration = timings.get(str(i + 1)).split(",")[1]
        a = subtitle(texts.get(str(i + 1)), start, duration)
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

def genSubBlock(subs: list [subtitle] ) -> bytes:
    """
    Injects the new text to the original data, returns the bytes. 
    Also returns the index we were at when we finished. 

    """ 
    newBlock = b''
    for i in range(len(subs) -1):
        length = struct.pack("I", len(bytes(subs[i])) + 4)
        newBlock += length + bytes(subs[i])
    
    # Add the last one
    newBlock += bytes(4) + bytes(subs[-1])
    
    return newBlock

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

def getDemoDiagHeader(data: bytes) -> bytes:
    """
    Returns the header portion only for a given dialogue section.
    """
    headerLength = struct.unpack("H", data[14:16])[0] + 4
    return data[:headerLength]

if debug:
    print(f'Only injecting Demo 25!')
    # bin_files = ['demoWorkingDir/usa/bins/demo-25.bin']

if __name__ == "__main__":
    """
    Main logic is here.
    """
    bin_files = ["demoWorkingDir/usa/bins/demo-79.bin"]
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
        origBlocks = len(origDemoData) // 0x800 # Use this later to check we hit the same length!
        demoDict: dict = injectTexts[basename][0]
        demoTimings: dict = injectTexts[basename][1]
        
        subtitles = assembleTitles(demoDict, demoTimings)

        offsets = DTE.getTextAreaOffsets(origDemoData)
        # nextStart = 1 # index of subtitle to encode. No longer needed.
        newDemoData = origDemoData[0 : offsets[0]] # UNTIL the header
        
        for Num in range(len(offsets)):
            oldHeader = getDemoDiagHeader(origDemoData[offsets[Num]:])
            oldLength = struct.unpack("H", oldHeader[1:3])[0]
            frameStart = struct.unpack("I", oldHeader[4:8])[0]
            frameLimit = struct.unpack("I", oldHeader[8:12])[0]
            # Get only subtitles in this section.
            subsForSection = []
            for sub in subtitles:
                if frameStart <= sub.startFrame < frameLimit:
                    subsForSection.append(sub)
            newSubBlock = genSubBlock(subsForSection) # TODO: CODE THIS DEF
            newLength = len(oldHeader) + len(newSubBlock)

            newHeader = bytes.fromhex("03") + struct.pack("H", newLength) + bytes(1) + struct.pack("II", frameStart, frameLimit) + oldHeader[12:16] + struct.pack("I", len(oldHeader) + len(newSubBlock) - 4) + oldHeader[20:]
            newDemoData += newHeader + newSubBlock
            # Add the rest of the data from this to the next offset OR until end of original demo. 
            if Num < len(offsets) - 1: # if it is NOT the last... 
                newDemoData += origDemoData[offsets[Num] + oldLength: offsets[Num + 1]]
            else:
                newDemoData += origDemoData[offsets[Num] + oldLength: ]
            # if debug:
            #     print(newSubBlock.hex(sep=" ", bytes_per_sep=4))
        
        # Buffer the demo to 0x800 block
        if len(newDemoData % 0x800) != 0:
            newDemoData += bytes(len(newDemoData) % 0x800)
        newBlocks = len(newDemoData) // 0x800
        # if debug:
        #     print(f'New data is {newBlocks} blocks, old was {origBlocks} blocks.')
        if newBlocks != origBlocks:
            print(f'BLOCK MISMATCH!\nNew data is {newBlocks} blocks, old was {origBlocks} blocks.\nTHERE COULD BE PROBLEMS IN RECOMPILE!!')

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