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
disc = 1

# Create a directory to store the extracted texts
# Get the files from the folder directory
inputDir = f'workingFiles/{version}-d{disc}/demo/bins'
outputDir = f'workingFiles/{version}-d{disc}/demo/texts'
os.makedirs(outputDir, exist_ok=True)
outputJsonFile = f"workingFiles/{version}-d{disc}/demo/demoText-{version}.json"

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
# if debug:
#     print(f'Only doing demo-1.bin!')
    # bin_files = [f'demoWorkingDir/{version}/bins/demo-25.bin']

def getTextHexes(textToAnalyze: bytes) -> tuple[list, bytes, list]: 
    """
    This just grabs all the text from each sector of the text area.
    We just grab the hex and return it. We also return the custom 
    character bytes at the end, which should always make a dictionary.
    """
    global debug
    
    #startingPoint = struct.unpack("<H", textToAnalyze[18:20])[0]
    
    segments = []
    # Coords = dict of Starting time, length to display
    coords = []
    # graphics are only for japanese vers. generally. init here so that we can pass back something even if no graphics found. 
    graphics = b'' 
    offset = 0

    # Search for the second pattern while looking for size pointers
    while offset < len(textToAnalyze):
        if debug:
            print(f'Offset: {offset}')
        # If loop to determine if we hit the last one. 
        if textToAnalyze[offset] == 0x00: # This is the last segment, always the same length? # TODO CLEAN THIS UP
            # All this nonsense finds the last segment since the length bytes are null.
            lastEnd = textToAnalyze.find(bytes.fromhex('00'), offset + 16)
            subset = textToAnalyze[offset: lastEnd]
            evenBytes = (4 - (len(subset) % 4))
            subset = textToAnalyze[offset: lastEnd + evenBytes]
            textSize = len(subset)
            # Get timings
            appearTime = struct.unpack("I", textToAnalyze[offset + 4: offset + 8])[0]
            appearDuration = struct.unpack("I", textToAnalyze[offset + 8: offset + 12])[0]
            coords.append(f'{appearTime},{appearDuration}')

            print(f'Final length = {textSize}') 
            segments.append(textToAnalyze[offset + 16: offset + textSize])
            graphics = textToAnalyze[offset + textSize: -4]
            break
        else:
            # Extract the double byte value (little-endian) as a pointer to the size
            textSize = struct.unpack('<H', textToAnalyze[offset:offset + 2])[0]
            appearTime = struct.unpack("I", textToAnalyze[offset + 4: offset + 8])[0]
            appearDuration = struct.unpack("I", textToAnalyze[offset + 8: offset + 12])[0]
            dialogueBytes = textToAnalyze[offset + 16: offset + textSize]

        # Append the size pointer and its offset to the list
        segments.append(dialogueBytes)
        coords.append(f'{appearTime},{appearDuration}')

        # Move to the next size pointer
        offset += textSize

    return segments, graphics, coords

def getTextAreaOffsets(demoData: bytes) -> list:
    """
    This is awful, but it should to a certain degree find demo offset spots.
    If there's a better way to do this lmk, but it's not too inefficient. 
    """
    patternA = b"\x03..." + b"...\x00" + b"....\x10\x00" # Figured out the universal pattern. 
    # 03 ?? ?? ?? ?? ?? ?? 00 ?? ?? ?? ?? 10 00 14 00 >> For IMHEX usage
    # patternB = bytes.fromhex("FF FF FF 7F 10 00") 
    # This is actually the indication a dialogue area runs to end of demo (until frame 0x7FFFFF)

    matches = re.finditer(patternA, demoData, re.DOTALL)
    offsets = [match.start() for match in matches]

    finalMatches = []
    for offset in offsets:
        # Extract size of the area
        length = struct.unpack('<H', demoData[offset + 1: offset + 3])[0]
        
        # This is just an alignment check. Last 4 should always be this constant.
        bytesToCheck = demoData[offset + length : offset + 4 + length] # 4 bytes at head are included.
        if bytesToCheck == bytes.fromhex("01 04 20 00"):
            finalMatches.append(offset)

    return finalMatches

def getTextAreaBytes(offset, demoData):
    """
    Returns the data from that offset found in the amount we expect 
    for processing. 
    """
    length = struct.unpack('<H', demoData[offset + 1: offset + 3])[0]
    exBuffer = struct.unpack('<H', demoData[offset + 14: offset + 16])[0] # Japanese has extra data here ?
    subset = demoData[offset + 4 + exBuffer: offset + 4 + length] # Includes the tail bytes 0x[01 04 20 00]

    return subset

def getDialogue(textHexes: list [bytes], graphicsData: bytes = None) -> list:
    global debug
    global filename
    global version
    
    dialogue = []

    if graphicsData is not None and filename is not None:
        demoDict = RD.makeCallDictionary(filename, graphicsData)
    else:
        demoDict = {}

    # Loop for all text, offsets, etc.
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
        textDict[f'{i:02}'] = text
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
        timings = [] # list of timings (start time, duration)
        timingCount = 1

        for offset in textOffsets:
            subset = getTextAreaBytes(offset, demoData)
            textHexes, graphicsBytes, coords = getTextHexes(subset)
            texts.extend(getDialogue(textHexes, graphicsBytes))
            timings.extend(coords)
        
        basename = filename.split('.')[0]
        demoScriptData[basename] = [textToDict(texts), textToDict(timings)]
        writeTextToFile(f'{outputDir}/{basename}.txt', texts)
        # writeTextToFile(f'{outputDir}/{basename}-timings.txt', timings) 
        
    with open(outputJsonFile, 'w') as f:
        f.write(json.dumps(demoScriptData, ensure_ascii=False))
        f.close()