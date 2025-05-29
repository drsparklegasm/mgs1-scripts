"""
This script is to analyze demo and vox files. 
We'll put out something like json/xml format 
for the entire demo/vox file.
"""

import os, sys, struct, re
import json
from xml.etree import ElementTree as ET
import translation.radioDict as RD

# For Vag Outputs
SAMPLE_RATES = {
    0x08: 22050,
    0x0C: 32000, 
    0xF0: 44100
}

class demo():
    """
    The demo class is a full polygon demo file. DEMO.DAT is filled with these.
    If a .dmo file is used, that's a single demo "object".
    """
    
    offset: int
    lengthInBlocks: int # size / 0x800.
    structure: ET.Element  # Try to make this match the XML output to a file.
    modified: bool 
    segments: list  # This is a list of segments in the demo. Use this for the structures. 
    
    def __init__(self, demoStartOffset: int = None, demoData: bytes = None, demoElement: ET.Element = None):
        """
        We can initialize either from an XML element, or from offset + demoData (raw byte data)
        """
        # Initialize as blank
        offset: int = 0 # This is only valid if analyzing the entire DEMO.DAT file, otherwise it is always 0.
        lengthInBlocks: int = 0 # size / 0x800
        structure: ET.Element = None # Try to make this match the XML output to a file.
        modified: bool = False
        segments: list = []         
        self.modified = False

        if demoElement == None and demoData is not None:
            # This one is for initializing from Binary
            self.offset = demoStartOffset
            self.structure = ET.Element("Demo", {
                "offset": str(self.offset),
                "modified": str(self.modified),
                "lengthInBlocks": str(len(demoData) // 0x800)
            })
            # This is a massive waste of space. 
            createXMLDemoData(self.structure, demoData)
            self.segments = parseDemoData(demoData)

        elif demoElement is not None: # TODO: THIS IS UNFINISHED!
            self.structure = demoElement
            self.modified = demoElement.get("modified")
            self.offset = demoElement.get("offset")
            # TODO: Create raw chunks
        else:
            print("Error! Failed to parse demo!")
            
        pass

    def toJson(self):
        """
        Returns a json item with the subs ONLY
        """
        sectionList = {}
        countA = 0
        for dialogueSection in self.structure.findall(".//captionChunk"):
            dialoguesList = {}
            countB = 0
            for caption in dialogueSection.findall(".//subtitle"):
                subtitle = {}
                subtitle["length"] = caption.get("length")
                subtitle["startFrame"] = caption.get("startFrame")
                subtitle["displayFrames"] = caption.get("displayFrames")
                # subtitle["buffer"] = caption.get("buffer")
                subtitle["text"] = caption.get("text")
                # subtitle["final"] = caption.get("final")
                dialoguesList[str(countB)] = subtitle
                countB += 1
            sectionList[str(countA)] = dialoguesList
            countA += 1
        
        return str(self.offset),  sectionList
    
    # Below functions return subset of the chunks
    def getAudioHeader(self): # -> audioHeader: # returns audioHeader
        for item in self.segments:
            if isinstance(item, audioHeader):
                return item
    
    def getAudioChunks(self) -> list:
        items = []
        for item in self.segments:
            if isinstance(item, audioChunk):
                items.append(item)
        return items
    
    def getDemoChunks(self) -> list:
        items = []
        for item in self.segments:
            if isinstance(item, demoChunk):
                items.append(item)
        return items
    
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
    kanjiDict: dict

    def __init__(self, data: bytes, characterDict: dict):
        self.kanjiDict = characterDict
        self.length, self.startFrame, self.displayFrames = struct.unpack("<III", data[0:12])
        self.buffer = data[12:16]
        if self.length == 0:
            self.final = True
            self.length = len(data)
        else:
            self.final = False
        self.text= RD.translateJapaneseHex(data[16:], characterDict) 
        return
    
    def toElement(self):
        """Convert the object into an XML Element."""
        dialogue = self.text.replace("\x00", "")
        elem = ET.Element("subtitle", {
                "length": str(self.length),
                "startFrame": str(self.startFrame),
                "displayFrames": str(self.displayFrames),
                "buffer": self.buffer.hex(),
                "text": str(dialogue),
                "final": str(self.final)
            }
        )
        return elem
    
class captionChunk():
    """Class to represent a caption chunk (dialogue data) found in a .dmo file."""
    magic: int
    length: int
    startFrame: int
    endFrame: int
    unknown: bytes # Usually 0x 10 00
    headerLength: int
    dialogueLength: int
    unknownChunk: bytes # This chunk is probably lip sync data.
    subtitles: list[dialogueLine]   # Initialize subtitles here ???
    kanjiDict: dict

    def __init__(self, data: bytes = None, element: ET.Element = None):
        """Initialize the caption chunk with data or an XML element."""
        self.subtitles = []
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
            self.parseSubtitles(subsData) # Parse the subtitles from the data
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
    
    def parseSubtitles(self, data: bytes) -> None: # Internal operation
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
    
    def toElement(self) -> ET.Element:
        """
        Convert the object into an XML Element.
        Automatically grabs the subtitles from the object.
        """
        elem = ET.Element("captionChunk")
        # My method:
        elem.set("magic", str(self.magic))
        elem.set("length", str(self.length))
        elem.set("startFrame", str(self.startFrame))
        elem.set("endFrame", str(self.endFrame))
        elem.set("unknown", self.unknown.hex())
        elem.set("headerLength", str(self.headerLength))
        elem.set("dialogueLength", str(self.dialogueLength))
        elem.set("unknownChunk", self.unknownChunk.hex())
        # Add subtitles
        for sub in self.subtitles:
            elem.append(sub.toElement())
        # Add kanjiDict
        kanjiDict_elem = ET.SubElement(elem, "kanjiDict")
        for key, value in self.kanjiDict.items():
            item_elem = ET.SubElement(kanjiDict_elem, "item", key=key)
            item_elem.text = str(value)

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
    magic: int
    length: int
    content: bytes
    
    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        return
    
    def toElement(self):
        elem = ET.Element("audioChunk", {
            "magic": str(self.magic),
            "length": str(self.length),
            "content": self.content.hex()
        })
        return elem

    
    def __str__(self):
        return f"Audio Chunk: {self.magic} Length: {self.length}"
    
class demoChunk():
    """Class to represent demo chunk (animation data) found in a .dmo file."""
    magic: int
    length: int
    content: bytes

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        return
    
    def toElement(self):
        """Convert the object into an XML Element."""
        elem = ET.Element("demoChunk", {
            "magic": str(self.magic),
            "length": str(self.length),
            "content": self.content.hex()
            }
        )
        return elem
    
    def __str__(self):
        return f"Demo Chunk: {self.magic} Length: {self.length} Content Length: {len(self.content)}"

class fileHeader():
    """Class to represent the header of the demo file."""
    magic: int
    length: int
    content: bytes

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        self.number = struct.unpack("<I", self.content)[0]
        return
    
    def toElement(self):
        """Convert the object into an XML Element."""
        elem = ET.Element("fileHeader", {
            "magic": str(self.magic),
            "length": str(self.length),
            "number": str(self.number),
            "content": self.content.hex()
            }
        )
        return elem
    
    def __str__(self):
        return f"File Header: {self.magic} Length: {self.length} Number: {self.number} Content Length: {len(self.content.hex())}"

class audioHeader():
    """Class to represent the header of the demo file."""
    magic: int
    length: int
    content: bytes
    dataLength: int
    sampleRate: int
    channels: int

    def __init__(self, data: bytes):
        self.magic = data[0]
        self.length = struct.unpack("<H", data[1:3])[0]
        self.content = data[4:self.length]
        self.dataLength = struct.unpack(">I", self.content[0:4])[0] # This particular value is big endian. Why? Who fucking knows. 
        self.sampleRate = SAMPLE_RATES.get(data[10], 0)
        self.channels = data[12]
        return
    
    def toElement(self):
        """Convert the object into an XML Element."""
        elem = ET.Element("audioHeader", {
            "magic": str(self.magic),
            "length": str(self.length),
            "dataLength": str(self.dataLength),
            "sampleRate": str(self.sampleRate),
            "channels": str(self.channels),
            "content": self.content.hex()
            }
        )
        return elem
    
    def __str__(self):
        return f"Audio Header: {self.magic} Length: {self.length} Sample Rate: {self.sampleRate} Channels: {self.channels} Content: {self.content.hex()}"

## TODO: This is unused, probably good to remove

# # Is this going to be the demo class?
# class demoParser():
#     """Class to parse demo files."""
#     demoData: bytes
#     demoXml: ET.Element
#     dialogues: list
#     kanji: dict

def parseDemoData(demoData: bytes) -> list:
    """
    Parse the demo data and return a list of dialogue lines.
    This really just does the list, we'll write another function for the XML.
    """
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

def createXMLDemoData(root: ET.Element, demoData: bytes):
    """
    Parse the demo data and return a list of dialogue lines.
    This really just does the list, we'll write another function for the XML."""
    # root = ET.Element("demoData")
    offset = 0
    while offset < len(demoData):
        chunkType = demoData[offset]
        length = struct.unpack("<H", demoData[offset + 1: offset + 3])[0]

        match chunkType:
            case 0xf0: # End chunk
                """End of file data"""
                root.append(ET.Element("endChunk", {
                    "type": str(chunkType), 
                    "length": str(length), 
                    "content": demoData[offset:offset + length].hex()
                    }
                ))
                break
            case 0x01: # This is an audio chunk
                root.append(audioChunk(demoData[offset:offset + length]).toElement())
            case 0x02:
                # This is an audio header info block
                root.append(audioHeader(demoData[offset:offset + length]).toElement())
            case 0x03:
                # This is a subtitle block
                root.append(captionChunk(demoData[offset:offset + length]).toElement())
            case 0x04:
                # This is a second language chunk, not sure what it does. TODO: Revisit when doing MGS Integral
                root.append(fileHeader(demoData[offset:offset + length]).toElement())
            case 0x05:
                # This is a demo/animation block
                root.append(demoChunk(demoData[offset:offset + length]).toElement())
            case 0x10:
                # This is a demo/animation block
                root.append(fileHeader(demoData[offset:offset + length]).toElement())
            case _:
                root.append("unknownChunk", {"type": str(chunkType), "length": str(length)})
                print(f"Unknown Type at offset {offset}: {chunkType} Length: {length}")
        # Prepare for next loop
        offset += length
    return root

def writeVagHeader(header: audioHeader, filename: str) -> bytes:
    """
    Filename is max 16 Bytes. Optional
    """
    # Write the header. VAGp for mono, VAGi for stereo interleaved
    if header.channels == 1:
        headerBytes: bytes = b"VAGp"
    elif header.channels == 2:   
        headerBytes: bytes = b"VAGi"
    else:
        print(f"Unknown channel type: {header.channels}. Defaulting to mono.")
        headerBytes: bytes = b"VAGp"
        return
    headerBytes += bytes.fromhex("00000003") # Version 3, static assignment for now # TODO: Check if always static
    headerBytes += bytes(4)
    headerBytes += struct.pack(">I", header.dataLength) # Data size
    headerBytes += struct.pack(">I", header.sampleRate) # Sample rate
    headerBytes += bytes(12)
    headerBytes += bytes(filename.split("/")[-1][:16], encoding="utf-8") # Filename 
    headerBytes += bytes(16-len(filename.split("/")[-1][:16])) # Filename
    headerBytes += bytes(64-len(headerBytes)) # Padding

    return headerBytes

def outputVagFile(demo: demo, filename: str, path: str = None):
    """
    Output the VAG file.
    Currently assumes only one audio file
    """
    # Fix formatting
    if path == None:
        path = ""
    if filename[-4:] == ".vag":
        filename = filename[:len(filename) - 4]

    # Get header bytes
    header = demo.getAudioHeader()
    headerBytes = writeVagHeader(header, filename)

    # Get data
    data: bytes = b""
    dataChunks = demo.getAudioChunks()
    for chunk in dataChunks:
        data += chunk.content
    
    # Write the file
    with open(f'{path}/{filename}.vag', "wb") as f:
        f.write(headerBytes)
        f.write(data)
        print(f"Outputted {filename} with {len(data)} bytes of data.")

    return f'{path}/{filename}.vag'
    
def splitVagChannels(demo: demo, filename: str, path: str = None) -> list[str]:
    """
    takes stereo vag data, outputs two mono audio file.
    Filename should NOT have extension.
    Returns single file if mono, dual if stereo. 
    """

    def stereoToMonoHeader(data: bytes) -> bytes:
        """
        Rewrites a stereo vag header as mono with half length
        """
        newData = b"VAGp" + data[4:12]
        # Fix length
        originalLength = struct.unpack(">I", data[12:16])[0]
        newLength = struct.pack(">I", originalLength // 2)
        newData += newLength
        # Add the rest of the header and return
        newData += header[16:]

        return newData
    
    headerBytes: bytes
    audioData: bytes
    secondChannelData: bytes # Right channel if stereo file
    if path == None:
        path = ""

    # Get the vag header 
    header = demo.getAudioHeader()
    headerBytes = writeVagHeader(header, filename)
    
    # Process audio chunks:
    chunks = demo.getAudioChunks()
    if header.channels == 1:
        for chunk in chunks:
            audioData += chunk.content
        with open(filename, 'rb') as f:
            f.write(headerBytes)
            f.write(audioData)
        return [f'{path}/{filename}.vag']

    # Swap magic bytes if we are stereo to a mono vag file
    elif header.channels == 2:
        headerBytes = stereoToMonoHeader(headerBytes)
        for chunk in chunks:
            audioData += chunk.content[:len(chunk.content) // 2]
            secondChannelData += chunk.content[len(chunk.content) // 2:]
        with open(f'{path}/{filename}-l.vag', 'rb') as f:
            f.write(headerBytes)
            f.write(audioData)
        with open(f'{path}/{filename}-r.vag', 'rb') as f:
            f.write(headerBytes)
            f.write(secondChannelData)
        return [f'{path}/{filename}-l.vag', f'{path}/{filename}-r.vag']
    else:
        print(f'Invalid number of channels! Channels: {header.channels}')
        return []

def parseDemoFile(filename: str):
    """
    Parse single or multiple demo files.
    """
    with open(filename, "rb") as f:
        demoData = f.read()
        demoItems = parseDemoData(demoData)
        print("Demo Items:")
        for item in demoItems:
            print(item)    


if __name__ == "__main__":
    # Check if the script is being run directly
    print("This script is not meant to be run directly.")
    

    """# Main loop to read and parse the demo/vox file
    demoFilename = "workingFiles/usa-d1/vox/bins/vox-0044.bin"
    with open(demoFilename, "rb") as f:
        demoData = f.read()
        demoItems = parseDemoData(demoData)
        print("Demo Items:")
        for item in demoItems:
            print(item)

    # Output the demo items to a text file for reference
    with open("workingFiles/vag-examples/demo.txt", "w") as f:
        for item in demoItems:
            f.write(str(item))
            f.write("\n")

    newFileName = demoFilename.split("/")[-1].split(".")[0] + ".vag"
    outputVagFile(demoItems, f"workingFiles/vag-examples/{newFileName}")"""

