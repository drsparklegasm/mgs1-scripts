"""
Recompiler for MGS RADIO.DAT files. This requires exported Radio XML and .json files created by RadioDatTools.py

Steps to use for translation:

1. Export XML and Json from RadioDatTools from source disk RADIO.DAT
2. Adjust dialogue in the .json file.
3. Run script with both files as arguments. 

We will output to RADIO.DAT or optionally a filename of your choice. 

"""

# ==== Dependencies ==== #

import os, struct
import radioDict 
import argparse
import xml.etree.ElementTree as ET

inputXML = 'extractedCallBins/1119995-decrypted.xml'
# inputXML = 'usaD1Analyze.xml'

radioSource = ET.parse(inputXML)

# ==== DEFS ==== #

# Large steps here
def realignOffsets():
    print(f'Offset integrity reviewed and done')

def createBinary():
    print(f'Binary data created')

def outputFile():
    print(f'File has been saved!')

# ==== Byte Encoding Defs ==== #

def getCallHeaderBytes(call: ET.Element) -> bytes:
    """
    Returns the bytes used for a call header. Should always return bytes object with length 11.
    """
    callHeader = b''
    attrs = call.attrib
    frequency = int(float(attrs.get("Freq")) * 100)
    freqBytes = struct.pack('>H', frequency)

    unk1 = bytes.fromhex(attrs.get("UnknownVal1"))
    unk2 = bytes.fromhex(attrs.get("UnknownVal2"))
    unk3 = bytes.fromhex(attrs.get("UnknownVal3"))
    lengthBytes = struct.pack('>H', int(attrs.get("Length")) - 9) # The header is 11 bytes, not in the length as shown in bytes

    # Assemble all pieces
    callHeader = freqBytes + unk1 + unk2 + unk3 + bytes.fromhex('80') + lengthBytes
    return callHeader

def getSubtitleBytes(subtitle: ET.Element) -> bytes:
    """
    Returns the hex for an entire subtitle command. Starts with FF01 and always ends with one null byte (\x00)
    It should be exclusively used within the getVoxBytes() def.
    """
    attrs = subtitle.attrib
    subtitleBytes = bytes.fromhex('ff01')
    lengthBytes = struct.pack('>H', int(attrs.get("length")) - 2) # TODO: Check this is equal to what we intend!
    face = bytes.fromhex(attrs.get("face"))
    anim = bytes.fromhex(attrs.get("anim"))
    unk3 = bytes.fromhex(attrs.get("unk3"))

    text = attrs.get("Text").encode('utf-8')
    text = text.replace(b'\x5c\x72\x5c\x6e' , b'\x80\x23\x80\x4e') # Replace \r\n with in-game byte codes for new lines

    subtitleBytes = subtitleBytes + lengthBytes + face + anim + unk3 + text + bytes.fromhex('00')
    return subtitleBytes

def getVoxBytes(vox: ET.Element) -> bytes:
    """
    Returns the hex for a VOX container (FF02). 
    Because it is a container that contains Subtitle elements, we will compile that hex here.

    """
    attrs = vox.attrib
    header = bytes.fromhex(attrs.get('Content'))
    
    subsContent = b''
    for sub in vox.findall('.//SUBTITLE'):
        subsContent = subsContent + getSubtitleBytes(sub)

    subsContent = subsContent + b'\x00' # there's always an extra null here.
    print(subsContent.hex())

    length = int(attrs.get("LengthB")) # TODO: Check this is equal to what we intend!
    headerLength = struct.unpack(">H", header[-2:len(header)])[0]
    print(length)
    print(headerLength)
    
    # Insert code that grabs all subtitle bytes

    voxBytes = header + subsContent

    return voxBytes

# Test code: Recompile call headers
for vox in radioSource.findall(".//VOX_CUES"):
    content = getVoxBytes(vox)
    print(content)
    print(content.hex())