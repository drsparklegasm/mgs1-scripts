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

demoScriptData: dict = {}

bar = progressbar.ProgressBar()

# Create a directory to store the extracted texts
# Get the files from the folder directory
inputDir = 'demoWorkingDir/jpn/bins'
outputDir = 'demoWorkingDir/jpn/texts'
outputJsonFile = "demoWorkingDir/jpn/demoText.json"

bin_files = glob.glob(os.path.join(inputDir, '*.bin'))
bin_files.sort(key=lambda f: int(f.split('-')[1].split('.')[0]))

os.makedirs(outputDir, exist_ok=True)
outputJsonFile = "demoWorkingDir/jpn/demoText.json"

# Define the first pattern to search for in hexadecimal
patternA = bytes.fromhex("3f ff 0c 00 02 01 00 00 00 00 00 00 10 08 00 00 03 00 00 00 04 08 00 00 01 00 00 00 03")
patternB = bytes.fromhex("ff ff ff 7f 10 00")
patternC = bytes.fromhex("0104 2000 0002")
patternD = bytes.fromhex("0104 2000")

# flags
debug = True

# List of files to skip (005.bin does not contain texts)
skipFilesList = ['005.bin']

# Set up progress bar
bar.maxval = len(bin_files)
barCount = 0
bar.start()

# DEBUG
if debug:
    print(f'Only doing demo-1.bin!')
    # bin_files = ['demoWorkingDir/jpn/bins/demo-1.bin']

def getTextOffsets(textToAnalyze: bytes) -> tuple[list, bytes]:
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
    """
    patternA = b".\x00\x00." + b"...\x00" + b"..\x00\x00..\x00\x00\x10\x00.."
    # ?? 00 00 ?? ?? ?? ?? 00 ?? ?? 00 00 ?? ?? 00 00 10 00 
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

# Loop through each .bin file in the folder
for bin_file in bin_files:
    # Skip files in the skip list
    filename = os.path.basename(bin_file)
    if filename in skipFilesList:
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
        length = struct.unpack('<H', demoData[offset + 5: offset + 7])[0]
        subset = demoData[offset: offset + 4 + length]
        textHexes, graphicsBytes = getTextOffsets(subset)
        texts.append(getDialogue(textHexes, graphicsBytes))
    

    """
    # Find the first pattern in the binary demoData
    offsetA = demoData.find(patternA)
    offsetB = demoData.find(patternB)
    offsetC = demoData.find(patternC)

    if debug:
        print(f'Found first pattern: {offsetA}')
        print(f'Found second pattern: {offsetB}')
        print(f'Found third pattern: {offsetC}')

    # Check if the first pattern was found
    if offsetA != -1:
        # Initialize offset with the initial pattern offset # 0x1B8 / 440
        lengthHeaderA: bytes = demoData[offsetA: offsetA + 32]
        totalLength = struct.unpack("<H", lengthHeaderA[-3:-1])[0]
        lengthHeaderB = demoData[offsetA + 32: offsetA + 64 ]
        # headerLength = struct.unpack("<H", textToAnalyze[10:12])[0]
        
        bytesToMatch = offsetA + 52
        bytesToMatchEnd = offsetC
        
        # This is the full thing after length A (0x160)
        textToAnalyze = demoData[offsetA + 32 : offsetA + 32 + totalLength]
        print(textToAnalyze[10:12])

        # Create a list to store size pointers and their offsets
        segments = getTextOffsets(textToAnalyze)
        offset, finalLength = segments[-1]
        graphicsData = textToAnalyze[offset + finalLength: -4]
        print(len(graphicsData) % 36)
        texts: list = getDialogue(segments, textToAnalyze, graphicsData)
    
    offsetB = demoData.find(patternB, offsetC)
    if offsetB != -1:
        print(f'More data was found! {bin_file}!')
        # video_data_size = int.from_bytes(demoData[offsetB + 6:offsetB + 8], byteorder='little')
        # print(f'Video data size: {video_data_size:x}')
        lengthOfText = struct.unpack('<H', demoData[offsetB + 8 :offsetB + 10])[0]
        textToAnalyze = demoData[ offsetB + 16 : offsetB + lengthOfText] 

        # Create a list to store size pointers and their offsets
        segments = getTextOffsets(textToAnalyze)
        texts.extend(getDialogue(segments, textToAnalyze, b""))
    """
    basename = filename.split('.')[0]
    demoScriptData[basename] = textToDict(texts)
    writeTextToFile(f'{outputDir}/{basename}.txt', texts)
    
with open(outputJsonFile, 'w') as f:
    f.write(json.dumps(demoScriptData))
    f.close()