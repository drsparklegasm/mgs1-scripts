"""
This script is to analyze demo and vox files. 
We'll put out something like json/xml format 
for the entire demo/vox file.
"""

import os, sys, struct, re
import json
from xml.etree import ElementTree as ET
import radioTools.radioDict as RD

class dialogueLine():
    """Class to represent a single line of dialogue in the demo file.
    Expects only the subtitle data. If it's the final in a chunk, need to find length
    """
    length: int
    startFrame: int
    displayFrames: int
    buffer: bytes
    text: str
    final: bool
    kanjiDict = {}

    def __init__(self, data: bytes, characterDict: dict):
        self.kanjiDict = characterDict
        self.length, self.startFrame, self.displayFrames = struct.unpack("<III", data[0:12])
        self.buffer = data[12:16]
        if self.length == 0:
            self.final = True
            self.length = len(data)
        self.text= data[16:].replace(b"\x00", b"").decode("utf-8") # Remove null bytes at end
        # self.text = RD.translateJapaneseHex(data[12:], self.kanjiDict)
        return
    
class captionChunk():
    """Class to represent a caption chunk (dialogue data) found in a .dmo file."""
    magic: bytes
    length: int
    startFrame: int
    endFrame: int
    unknown: bytes # Usually 0x 10 00
    headerLength: int
    dialogueLength: int
    unknownChunk: bytes # This chunk is probably lip sync data.
    subtitles: list[dialogueLine]
    kanjiDict: dict

    def parseSubtitles(data: bytes, characterDict: dict):
        """Returns a list of the dialogue lines in the chunk."""
        offset = 0
        subsList = []
        while offset < len(data):
            subLength = struct.unpack("<I", data[offset:offset + 4])[0]
            if subLength == 0: # Last line is always 0 length
                subsList.append(dialogueLine(data[offset:], characterDict))
                break
            subsList.append(dialogueLine(data[offset:offset + subLength], characterDict))
            offset += subLength

        # Return the list of dialogue lines
        return subsList

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.startFrame = struct.unpack("<I", data[4:8])[0]
        self.endFrame = struct.unpack("<I", data[8:12])[0]
        self.unknown = data[12:14]
        self.headerLength = struct.unpack("<H", data[14:16])[0]
        self.dialogueLength = struct.unpack("<H", data[16:18])[0] # Runs until end of dialogue. 
        self.unknownChunk = data[18:self.headerLength + 4] # This chunk is probably lip sync data.
        # At this point we grab kanji graphics and make a dict. Keep an exception for no graphics data.
        graphicsData = data[self.dialogueLength + 4:self.length] # Safer to limit the length of the data.
        if len(graphicsData) > 0:
            self.kanjiDict = RD.makeCallDictionary("demo", graphicsData)
        else:
            self.kanjiDict = {}
        # Now that we have a dict, we can parse the subtitles.
        self.subtitles = self.parseSubtitles(data[self.headerLength + 4:self.dialogueLength + 4], self.kanjiDict)
        
        return
    
    def __str__(self):
        return f"Caption Chunk: {self.magic} Length: {self.length} Start Frame: {self.startFrame} End Frame: {self.endFrame} Unknown: {self.unknown} Header Length: {self.headerLength} Dialogue Length: {self.dialogueLength} Unknown Chunk: {self.unknownChunk} Subtitles: {len(self.subtitles)}"
    
    def __print__(self):
        """Print the object in a readable format."""
        print(f"Caption Chunk: {self.magic} Length: {self.length} Start Frame: {self.startFrame} End Frame: {self.endFrame} Unknown: {self.unknown} Header Length: {self.headerLength} Dialogue Length: {self.dialogueLength} Unknown Chunk: {self.unknownChunk}")
        for sub in self.subtitles:
            print(f"  Subtitle: {sub.text}")
        return

    
class demoChunk():
    """Class to represent demo chunk (animation data) found in a .dmo file."""
    magic: bytes
    length: int
    content: bytes

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        return

class header():
    """Class to represent the header of the demo file."""
    magic: bytes
    length: int
    content: bytes

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        return

class demoParser():
    """Class to parse demo files."""
    demoData: bytes
    demoXml: ET.Element
    dialogues: list
    kanji: dict

def parseDemoData(demoData: bytes):
    """Parse the demo data and return a list of dialogue lines."""
    items = []
    offset = 0
    while offset < len(demoData):
        chunkType = demoData[offset]
        length = struct.unpack("<H", demoData[offset + 1: offset + 3])[0]

        match chunkType:
            case 0xf0:
                """End of file data"""
                break
            case 0x03:
                # This is a subtitle block
                items.append(captionChunk(demoData[offset:offset + length]))
            case _:
                items.append(f"Unknown Type: {type} Length: {length}")
        # Prepare for next loop
        offset += length

    return items

demoFilename = "workingFiles/usa-d1/demo/newBins/demo-01.bin"
with open(demoFilename, "rb") as f:
    demoData = f.read()
    demoItems = parseDemoData(demoData)
    print("Demo Items:")
    for item in demoItems:
        print(item)

if __name__ == "__main__":
    # Check if the script is being run directly
    print("This script is not meant to be run directly.")

