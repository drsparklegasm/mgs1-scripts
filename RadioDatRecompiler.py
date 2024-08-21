"""
Recompiler for MGS RADIO.DAT files. This requires exported Radio XML and .json files created by RadioDatTools.py

Steps to use for translation:

1. Export XML and Json from RadioDatTools from source disk RADIO.DAT
2. Adjust dialogue in the .json file.
3. Run script with both files as arguments. 

We will output to RADIO.DAT or optionally a filename of your choice. 

"""

"""
To do list:
TODO: Methods for integrity check against original bin file
TODO: Element checker
TODO: Binary compilers for other methods. 
TODO: Handle nulls somehow. 
"""

# ==== Dependencies ==== #

import os, struct
import radioDict 
import argparse
import xml.etree.ElementTree as ET

# inputXML = 'extractedCallBins/1119995-decrypted.xml'
inputXML = 'usaD1Analyze.xml'

radioSource = ET.parse(inputXML)

checkBinFile = 'extractedCallBins/1119995.bin'
callToCheck = open(checkBinFile, 'rb').read()

# ==== DEFS ==== #

# Large steps here
def realignOffsets():
    print(f'Offset integrity reviewed and done')

def createBinary():
    print(f'Binary data created')

def outputFile():
    print(f'File has been saved!')

# ==== Byte Encoding Defs ==== #

def getFreqbytes(freq: str) -> bytes:
    frequency = int(float(freq) * 100)
    freqBytes = struct.pack('>H', frequency)
    return freqBytes

def getCallHeaderBytes(call: ET.Element) -> bytes:
    """
    Returns the bytes used for a call header. Should always return bytes object with length 11.
    """
    callHeader = b''
    attrs = call.attrib
    freq = getFreqbytes(attrs.get('Freq'))
    unk1 = bytes.fromhex(attrs.get("UnknownVal1"))
    unk2 = bytes.fromhex(attrs.get("UnknownVal2"))
    unk3 = bytes.fromhex(attrs.get("UnknownVal3"))
    lengthBytes = struct.pack('>H', int(attrs.get("Length")) - 9) # The header is 11 bytes, not in the length as shown in bytes

    # Assemble all pieces
    callHeader = freq + unk1 + unk2 + unk3 + bytes.fromhex('80') + lengthBytes
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

    text = attrs.get("text").encode('utf-8')
    text = text.replace(b'\x5c\x72\x5c\x6e' , b'\x80\x23\x80\x4e') # Replace \r\n with in-game byte codes for new lines

    subtitleBytes = subtitleBytes + lengthBytes + face + anim + unk3 + text + bytes.fromhex('00')
    return subtitleBytes

def getVoxBytes(vox: ET.Element) -> bytes:
    """
    Returns the hex for a VOX container (FF02). 
    Because it is a container that contains Subtitle elements, we will compile that hex here.

    TODO: MUS_CUES and ANI_FACE could both be included here. We'll need to figure out 
    how to identify the type of element and return the correct hex. 
    """
    attrs = vox.attrib
    header = bytes.fromhex(attrs.get('content'))

    subsContent = b''

    binary = b''
    for child in vox:
        print(child.tag)
        binary = handleElement(child)
        print(binary)
        subsContent = subsContent + binary
    
    """
    for sub in vox.findall('.//SUBTITLE'):
        subsContent = subsContent + getSubtitleBytes(sub)
    """

    subsContent = subsContent + b'\x00' # there's always an extra null here.
    print(subsContent.hex())

    length = int(attrs.get("lengthB")) # TODO: Check this is equal to what we intend!
    headerLength = struct.unpack(">H", header[-2:len(header)])[0]
    print(length)
    print(headerLength)
    
    # Insert code that grabs all subtitle bytes

    voxBytes = header + subsContent
    return voxBytes

def getAnimBytes(mus: ET.Element) -> bytes: 
    """
    Animation hex command 0xFF03
    """
    attrs = mus.attrib

    animBytes = bytes.fromhex('FF03')
    length = int(attrs.get('length')) - 2
    face = bytes.fromhex(attrs.get('face'))
    anim = bytes.fromhex(attrs.get('anim'))
    buff = bytes.fromhex(attrs.get('buff'))
    
    if length == 8:
        animBytes =  animBytes + struct.pack('>H', length) + face + anim + buff
    
    return animBytes

def getFreqAddBytes(elem: ET.Element) -> bytes:
    """
    freq-add hex command 0xFF04
    """
    attrs = elem.attrib

    elemBytes = bytes.fromhex('FF04')
    length = int(attrs.get('length')) - 2
    
    freq = getFreqbytes(attrs.get('freq'))
    name = attrs.get('name').encode('utf8')
    
    if length == 8:
        elemBytes =  elemBytes + struct.pack('>H', length) + freq + name + b'\x00'
    
    return elemBytes

def getContentBytes(elem: ET.Element) -> bytes: 
    """
    This one is to get binary when we specifically mark a 'content' field.
    =====
    Full list of what this works for:
    - FF06, FF07, FF08
    """
    name = elem.tag
    attrs = elem.attrib
    """
    # We may not need this but if we need the name it's elem.tag
    match name:
        case "MUS_CUES":
            elemBytes = bytes.fromhex('FF06')
        case "ASK_USER":
            elemBytes = bytes.fromhex('FF07')
        case "SAVEGAME":
            elemBytes = bytes.fromhex('FF08')
    

    length = int(attrs.get('length')) - 2
    face = bytes.fromhex(attrs.get('face'))
    anim = bytes.fromhex(attrs.get('anim'))
    buff = bytes.fromhex(attrs.get('buff'))
    
    if length == 8:
        animBytes =  animBytes + struct.pack('>H', length) + face + anim + buff

    """
    elemBytes = bytes.fromhex(attrs.get('content'))

    return elemBytes

def handleElement(elem: ET.Element) -> bytes:

    binary = b''
    match elem.tag:
        case 'SUBTITLE':
            binary = getSubtitleBytes(elem)
        case 'VOX_CUES': 
            binary = getVoxBytes(elem)
        case 'ANI_FACE': 
            binary = getAnimBytes(elem)
        case 'ADD_FREQ':
            binary = getFreqAddBytes(elem)
        case 'MEM_SAVE' | 'MUS_CUES' | 'ASK_USER': 
            binary = getContentBytes(elem)
        case 'SAVEGAME':
            print(f'{elem.tag} NOT YET IMPLEMENTED')
        case 'IF_CHECK': 
            print(f'{elem.tag} NOT YET IMPLEMENTED')
        case 'ELSE': 
            print(f'{elem.tag} NOT YET IMPLEMENTED')
        case 'ELSE_IFS':
            print(f'{elem.tag} NOT YET IMPLEMENTED')
        case 'SWITCH':
            print(f'{elem.tag} NOT YET IMPLEMENTED')
        case 'SWITCHOP':
            print(f'{elem.tag} NOT YET IMPLEMENTED')
        case 'EVAL_CMD':
            print(f'{elem.tag} NOT YET IMPLEMENTED')
        case 'NULL':
            binary = b'\x00'
    
    return binary

# Test code: Recompile call headers

for vox in radioSource.findall(".//VOX_CUES"):
    content = getVoxBytes(vox)
    """print(content)
    if content in callToCheck:
        continue
    else:
        print(f'Didn\'t work!')
        print(vox)"""