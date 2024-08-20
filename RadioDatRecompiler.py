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

# inputXML = 'extractedCallBins/1119995-decrypted.xml'
inputXML = 'usaD1Analyze.xml'

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
    """
    attrs = subtitle.attrib
    subtitleBytes = bytes.fromhex('ff01')
    




# Test code: Recompile call headers
for call in radioSource.findall(".//Call"):
    bytesToPrint = getCallHeaderBytes(call)
    print(bytesToPrint.hex())