"""
This script is to analyze demo and vox files. 
We'll put out something like json/xml format 
for the entire demo/vox file.
"""

import os, sys, struct, re
import json
from xml.etree import ElementTree as ET
import radioTools.radioDict as RD

sampleRates = {
    0x08: 22050,
    0x0C: 32000, 
    0xF0: 44100
}

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
        self.text= RD.translateJapaneseHex(data[16:], characterDict) 
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
    subtitles: list[dialogueLine] = []  # Initialize subtitles here
    kanjiDict: dict

    def __init__(self, data: bytes = None, element: ET.Element = None):
        """Initialize the caption chunk with data or an XML element."""
        if data is not None:
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
            subsData = data[self.headerLength + 4:self.dialogueLength + 4]
            self.parseSubtitles(subsData)
        elif element is not None and data is None:
            # Initialize from XML Element
            self.magic = int(element.get("magic"))
            self.length = int(element.get("length"))
            self.startFrame = int(element.get("startFrame"))
            self.endFrame = int(element.get("endFrame"))
            self.unknown = bytes.fromhex(element.get("unknown").replace("0x", "").zfill(4))
            self.headerLength = int(element.get("headerLength"))
            self.dialogueLength = int(element.get("dialogueLength"))
            self.unknownChunk = bytes.fromhex(element.find("unknownChunk").text.replace("0x", ""))
            
            kanjiDict_elem = element.find("kanjiDict")
            if kanjiDict_elem is not None:
                self.kanjiDict = {item.get("key"): item.text for item in kanjiDict_elem.findall("item")}
            else:
                self.kanjiDict = {}
                
            subtitles_elem = element.find("subtitles")
            self.subtitles = []
            if subtitles_elem is not None:
                for sub_elem in subtitles_elem.findall("dialogueLine"):
                    subtitle = dialogueLine(b"", characterDict=self.kanjiDict)
                    subtitle.length = int(sub_elem.get("length"))
                    subtitle.startFrame = int(sub_elem.get("startFrame"))
                    subtitle.displayFrames = int(sub_elem.get("displayFrames"))
                    subtitle.text = sub_elem.get("text")
                    self.subtitles.append(subtitle)
        else:
            raise ValueError("Either data or element must be provided, but not both.")
        
        return
    
    def parseSubtitles(self, data: bytes) -> list[dialogueLine]:
        """Returns a list of the dialogue lines in the chunk."""
        offset = 0
        while offset < len(data):
            subLength = struct.unpack("<I", data[offset:offset + 4])[0]
            if subLength == 0: # Last line is always 0 length
                self.subtitles.append(dialogueLine(data[offset:], self.kanjiDict))
                break
            self.subtitles.append(dialogueLine(data[offset:offset + subLength], self.kanjiDict))
            offset += subLength
        return
    
    def __toElem__(self):
        """Convert the object into an XML Element."""
        elem = ET.Element("captionChunk")
        for attr, value in self.__dict__.items():
            if attr == "subtitles":
                subtitles_elem = ET.SubElement(elem, "subtitles")
                for subtitle in self.subtitles:
                    sub_elem = ET.SubElement(subtitles_elem, "dialogueLine")
                    sub_elem.set("length", str(subtitle.length))
                    sub_elem.set("startFrame", str(subtitle.startFrame))
                    sub_elem.set("displayFrames", str(subtitle.displayFrames))
                    sub_elem.set("text", subtitle.text)
            elif attr == "kanjiDict":
                # Assuming kanjiDict is a dictionary of strings
                kanjiDict_elem = ET.SubElement(elem, "kanjiDict")
                for key, value in self.kanjiDict.items():
                    item_elem = ET.SubElement(kanjiDict_elem, "item", key=key)
                    item_elem.text = str(value)
            else:
                elem.set(attr, str(value))

        return elem
    
    def __str__(self):
        return f"Caption Chunk: {self.magic} Length: {self.length} Start Frame: {self.startFrame} End Frame: {self.endFrame} Unknown: {self.unknown} Header Length: {self.headerLength} Dialogue Length: {self.dialogueLength} Unknown Chunk: {self.unknownChunk} Subtitles: {len(self.subtitles)}"
    
    def __print__(self):
        """Print the object in a readable format."""
        print(f"Caption Chunk: {self.magic} Length: {self.length} Start Frame: {self.startFrame} End Frame: {self.endFrame} Unknown: {self.unknown} Header Length: {self.headerLength} Dialogue Length: {self.dialogueLength} Unknown Chunk: {self.unknownChunk}")
        for sub in self.subtitles:
            print(f"  Subtitle: {sub.text}")
        return

class audioChunk():
    magic: bytes
    length: int
    content: bytes
    
    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        return
    
    def __toElem__(self):
        """Convert the object into an XML Element."""
        elem = ET.Element("audioChunk")
        for attr, value in self.__dict__.items():
            elem.set(attr, str(value))

        return elem
    
    def __str__(self):
        return f"Audio Chunk: {self.magic} Length: {self.length}"
    
class demoChunk():
    """Class to represent demo chunk (animation data) found in a .dmo file."""
    magic: bytes
    length: int
    content: bytes

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length].hex()
        return
    
    def __toElem__(self):
        """Convert the object into an XML Element."""
        elem = ET.Element("demoChunk")
        for attr, value in self.__dict__.items():
            elem.set(attr, str(value))

        return elem
    def __str__(self):
        return f"Demo Chunk: {self.magic} Length: {self.length} Content Length: {len(self.content)}"

class fileHeader():
    """Class to represent the header of the demo file."""
    magic: bytes
    length: int
    content: bytes

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        self.number = struct.unpack("<I", self.content)[0]
        return
    
    def __toElem__(self):
        """Convert the object into an XML Element."""
        elem = ET.Element("header")
        for attr, value in self.__dict__.items():
            elem.set(attr, str(value))

        return elem
    
    def __str__(self):
        return f"File Header: {self.magic} Length: {self.length} Number: {self.number} Content Length: {len(self.content.hex())}"

class audioHeader():
    """Class to represent the header of the demo file."""
    magic: bytes
    length: int
    content: bytes
    dataLength: int
    sampleRate: int
    channels: int

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        self.dataLength = struct.unpack("<I", self.content[4:8])[0]
        self.sampleRate = sampleRates.get(data[10], 0)
        self.channels = data[12]
        return
    
    def __toElem__(self):
        """Convert the object into an XML Element."""
        elem = ET.Element("header")
        for attr, value in self.__dict__.items():
            elem.set(attr, str(value))

        return elem
    
    def __str__(self):
        return f"Audio Header: {self.magic} Length: {self.length} Sample Rate: {self.sampleRate} Channels: {self.channels} Content: {self.content.hex()}"

class demoParser():
    """Class to parse demo files."""
    demoData: bytes
    demoXml: ET.Element
    dialogues: list
    kanji: dict

def parseDemoData(demoData: bytes):
    """
    Parse the demo data and return a list of dialogue lines.
    This really just does the list, we'll write another function for the XML."""
    items = []
    offset = 0
    while offset < len(demoData):
        chunkType = demoData[offset]
        length = struct.unpack("<H", demoData[offset + 1: offset + 3])[0]

        match chunkType:
            case 0xf0: # End chunk
                """End of file data"""
                break
            case 0x01: # This is an audio chunk
                items.append(audioChunk(demoData[offset:offset + length]))
            case 0x02:
                # This is an audio header info block
                items.append(audioHeader(demoData[offset:offset + length]))
            case 0x03:
                # This is a subtitle block
                items.append(captionChunk(demoData[offset:offset + length]))
            case 0x04:
                # This is a second language chunk, not sure what it does. Revisit when doing MGS Integral
                items.append(fileHeader(demoData[offset:offset + length]))
            case 0x05:
                # This is a demo/animation block
                items.append(demoChunk(demoData[offset:offset + length]))
            case 0x10:
                # This is a demo/animation block
                items.append(fileHeader(demoData[offset:offset + length]))
            case _:
                items.append(f"Unknown Type: {chunkType} Length: {length}")
        # Prepare for next loop
        offset += length
    return items

def outputVagFile(items: list, filename: str):
    """Output the VAG file."""
    header: audioHeader
    data: bytes = b""
    with open(filename, "wb") as f:
        for item in items:
            if isinstance(item, audioChunk):
                data += item.content
            elif isinstance(item, audioHeader):
                header = item
            else:
                continue

        # Write the header. VAGp for mono, VAGi for stereo interleaved
        if header.channels == 1:
            headerBytes: bytes = b"VAGp"
        elif header.channels == 2:   
            headerBytes: bytes = b"VAGi"
        else:
            print(f"Unknown channel type: {header.channels}. Defaulting to mono.")
            headerBytes: bytes = b"VAGp"
            return
        headerBytes += bytes.fromhex("00000003") # Version 3, static assignment for now
        headerBytes += bytes(4)
        headerBytes += struct.pack(">I", header.dataLength + 64) # Data size
        headerBytes += struct.pack(">I", header.sampleRate) # Sample rate
        headerBytes += bytes(12)
        headerBytes += bytes(filename[:16], encoding="utf-8") # Filename 
        headerBytes += bytes(16-len(filename.split(".", -1)[:16])) # Filename
        headerBytes += bytes(64-len(headerBytes)) # Padding

        f.write(headerBytes)
        f.write(data)
        print(f"Outputted {filename} with {len(data)} bytes of data.")
        return

demoFilename = "workingFiles/usa-d1/vox/bins/vox-0029.bin"
with open(demoFilename, "rb") as f:
    demoData = f.read()
    demoItems = parseDemoData(demoData)
    print("Demo Items:")
    for item in demoItems:
        print(item)

with open("demo.txt", "w") as f:
    for item in demoItems:
        f.write(str(item))
        f.write("\n")

outputVagFile(demoItems, "workingFiles/vag-examples/demo.vag")

        
if __name__ == "__main__":
    # Check if the script is being run directly
    print("This script is not meant to be run directly.")

