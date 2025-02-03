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

import os, sys
sys.path.append(os.path.abspath('./myScripts'))
import re
import glob
import struct
import progressbar
import radioTools.radioDict as RD
import json

demoScriptData: dict = {}

bar = progressbar.ProgressBar()

version = "usa"
version = "jpn"

# Create a directory to store the extracted texts
# Get the files from the folder directory
inputDir = f'demoWorkingDir/{version}/bins'
outputDir = f'demoWorkingDir/{version}/texts'
os.makedirs(outputDir, exist_ok=True)
outputJsonFile = f"demoWorkingDir/{version}/demoText-{version}.json"

# Grab all files in the directory and sort into order.
bin_files = glob.glob(os.path.join(inputDir, '*.bin'))
bin_files.sort(key=lambda f: int(f.split('-')[1].split('.')[0]))

# flags
debug = True

# List of files to skip (Ex: 005.bin does not contain texts)
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

# Set up progress bar
bar.maxval = len(bin_files)
barCount = 0
bar.start()

# DEBUG
if debug:
    print(f'Only doing demo-1.bin!')
    # bin_files = [f'demoWorkingDir/{version}/bins/demo-1.bin']

def getTextHexes(textToAnalyze: bytes) -> tuple[list, bytes]: 
    """
    This just grabs all the text from each sector of the text area.
    We just grab the hex and return it. We also return the custom 
    character bytes at the end, which should always make a dictionary.
    """
    global debug
    
    startingPoint = struct.unpack("<H", textToAnalyze[18:20])[0]
    
    segments = []
    offset = startingPoint + 8
    # Search for the second pattern while looking for size pointers
    while offset < len(textToAnalyze):
        if debug:
            print(f'Offset: {offset}')
        if textToAnalyze[offset] == 0x00: # This is the last segment, always the same length? # TODO CLEAN THIS UP
            lastEnd = textToAnalyze.find(bytes.fromhex('00'), offset + 16)

            subset = textToAnalyze[offset: lastEnd]
            evenBytes = (4 - (len(subset) % 4))
            subset = textToAnalyze[offset: lastEnd + evenBytes]
            textSize = len(subset)

            print(f'Final length = {textSize}') 
            segments.append(textToAnalyze[offset + 16: offset + textSize])
            graphics = textToAnalyze[offset + textSize: ]
            break
        else:
            # Extract the double byte value (little-endian) as a pointer to the size
            textSize = struct.unpack('<H', textToAnalyze[offset:offset + 2])[0]
            dialogueBytes = textToAnalyze[offset + 16: offset + textSize]

        # Append the size pointer and its offset to the list
        segments.append(dialogueBytes)

        # Move to the next size pointer
        offset += textSize

    return segments, graphics

def getTextAreaOffsets(demoData: bytes) -> list:
    """
    This is awful, but it should to a certain degree find demo offset spots.
    If there's a better way to do this lmk, but it's not too inefficient. 
    """
    patternA = b".\x00\x00." + b"...\x00" + b"..\x00\x00..\x00\x00\x10\x00.."
    # ?? 00 00 ?? ?? ?? ?? 00 ?? ?? 00 00 ?? ?? 00 00 10 00 >> For IMHEX usage
    patternB = bytes.fromhex("FF FF FF 7F 10 00")

    matches = re.finditer(patternA, demoData, re.DOTALL)
    offsets = [match.start() for match in matches]

    finalMatches = []
    for offset in offsets:
        lengthBytes = demoData[offset + 5: offset + 7]
        length = struct.unpack('<H', lengthBytes)[0]
        bytesToCheck = demoData[offset + 4 + length : offset + 8 + length]
        if bytesToCheck == bytes.fromhex("01 04 20 00"):
            finalMatches.append(offset)
    if demoData.find(patternB) != -1:
        finalMatches.append(demoData.find(patternB) - 12) # This pattern 12 bytes later than other matches

    return finalMatches

def getTextAreaBytes(offset, demoData):
    """
    Returns the data from that offset found in the amount we expect 
    for processing. 
    """
    length = struct.unpack('<H', demoData[offset + 5: offset + 7])[0]
    subset = demoData[offset: offset + 4 + length]

    return subset

def getDialogue(textHexes: list, graphicsData: bytes) -> list:
    global debug
    global filename

    dialogue = []
    demoDict = RD.makeCallDictionary(filename, graphicsData)
    for dialogueHex in textHexes:
            text = RD.translateJapaneseHex(dialogueHex, demoDict)
            # text = text.encode(encoding='utf8', errors='ignore')
            if debug:
                print(text)
            text = text.replace('\x00', "")
            dialogue.append(text)
    return dialogue

def textToDict(dialogue: list) -> dict:
    i = 1
    textDict = {}
    for text in dialogue:
        textDict[i] = text
        i += 1
    
    return textDict
            
def writeTextToFile(filename: str, dialogue: list) -> None:
    global debug
    with open(filename, 'w', encoding='utf8') as f:
        for text in dialogue:
            f.write(f'{text}\n')
        f.close()

def findOffsets(byteData: bytes, pattern: bytes) -> list:
    """
    Find patterns in the byte data. 
    """
    foundPatterns = []
    offset = 0
    while offset != -1:
        offset = byteData.find(pattern, offset)
        if offset != -1:
            foundPatterns.append(pattern)
    return foundPatterns

if __name__ == "__main__":
    # Loop through each .bin file in the folder
    for bin_file in bin_files:
        # Skip files in the skip list
        filename = os.path.basename(bin_file)

        # Manual override to skip certain demos
        if filename in skipFilesListD1:
            continue

        if debug:
            print(f"Processing file: {bin_file}")

        # Open the binary file for reading in binary mode
        with open(bin_file, 'rb') as binary_file:
            demoData = binary_file.read()
        
        textOffsets = getTextAreaOffsets(demoData)

        print(f'{os.path.basename(bin_file)}: {textOffsets}')

        texts = []

        for offset in textOffsets:
            subset = getTextAreaBytes(offset, demoData)
            textHexes, graphicsBytes = getTextHexes(subset)
            texts.extend(getDialogue(textHexes, graphicsBytes))
        
        basename = filename.split('.')[0]
        demoScriptData[basename] = textToDict(texts)
        writeTextToFile(f'{outputDir}/{basename}.txt', texts)
        
    with open(outputJsonFile, 'w') as f:
        f.write(json.dumps(demoScriptData, ensure_ascii=False))
        f.close()