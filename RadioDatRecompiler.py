"""
Recompiler for MGS RADIO.DAT files. This requires exported Radio XML and .json files created by RadioDatTools.py

Steps to use for translation:

1. Export XML and Json from RadioDatTools from source disk RADIO.DAT
2. Adjust dialogue in the .json file.
3. Run script with both files as arguments. 

We will output to RADIO.DAT or optionally a filename of your choice. 


To do list:

TODO: Element checker
TODO: Need logic to re-insert b'\x80' before each punctuation mark that needs it

"""

# ==== Dependencies ==== #

import os, struct
import radioDict 
import argparse
import xml.etree.ElementTree as ET

subUseOriginalHex = False

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
    global subUseOriginalHex

    attrs = subtitle.attrib
    subtitleBytes = bytes.fromhex('ff01')
    lengthBytes = struct.pack('>H', int(attrs.get("length")) - 2) # TODO: Check this is equal to what we intend!
    face = bytes.fromhex(attrs.get("face"))
    anim = bytes.fromhex(attrs.get("anim"))
    unk3 = bytes.fromhex(attrs.get("unk3"))

    text = attrs.get("text").encode('utf-8')
    text = text.replace(b'\x5c\x72\x5c\x6e' , b'\x80\x23\x80\x4e') # Replace \r\n with in-game byte codes for new lines
    if not subUseOriginalHex:
        text = text.replace(bytes.fromhex("22") , bytes.fromhex("8022")) 

    if subUseOriginalHex:
        subtitleBytes = subtitleBytes + lengthBytes + face + anim + unk3 + bytes.fromhex(attrs.get('textHex')) 
    else:
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
    binary = bytes.fromhex(attrs.get('content'))

    for child in vox:
        # print(child.tag)
        binary += handleElement(child)
    
    binary += bytes.fromhex('00')
    # there's always an extra null here.
    # print(subsContent.hex())
    """
    length = int(attrs.get("lengthB")) # TODO: Check this is equal to what we intend!
    headerLength = struct.unpack(">H", header[-2:len(header)])[0]
    """
    return binary

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
    This one is to get binary when we specifically mark a 'content' field. Full list of what this works for:
    FF04, FF05, FF06, FF07, FF08
    """
    attrs = elem.attrib
    elemBytes = bytes.fromhex(attrs.get('content'))

    return elemBytes

def getContainerContentBytes(elem: ET.Element) -> bytes:
    """
    The equivelant of Handle element. 
    """
    binary = b''
    for subelem in elem:
        binary = binary + handleElement(subelem)
    binary += bytes.fromhex('00')

    return binary



def handleElement(elem: ET.Element) -> bytes:
    """
    Takes an element and returns the bytes for that element and all subelements. 
    """
    binary = b''
    attrs = elem.attrib
    match elem.tag:
        case 'SUBTITLE':
            # ff01
            binary = getSubtitleBytes(elem)
        case 'VOX_CUES': 
            # ff02
            binary = getVoxBytes(elem)
        # case 'ADD_FREQ':
            # binary = getFreqAddBytes(elem)
        case 'ANI_FACE' | 'ADD_FREQ' | 'MEM_SAVE' | 'MUS_CUES' | 'ASK_USER' | 'SAVEGAME' | 'EVAL_CMD': 
            # ff03-08, FF40
            binary = getContentBytes(elem)
        case 'IF_CHECK': 
            binary = bytes.fromhex(attrs.get('content'))
            binary += getContainerContentBytes(elem)
            # Troubleshooting
            """print(attrs.get('length'))
            print(len(binary))"""
        case 'THEN_DO': 
            binary += getContainerContentBytes(elem)
        case 'ELSE': 
            binary = bytes.fromhex(attrs.get('content'))
            binary += getContainerContentBytes(elem)
        case 'ELSE_IFS':
            binary = bytes.fromhex(attrs.get('content'))
            binary += getContainerContentBytes(elem)
        case 'RND_SWCH':
            binary = bytes.fromhex(attrs.get('content'))
            binary += getContainerContentBytes(elem)
        case 'RND_OPTN':
            binary = bytes.fromhex(attrs.get('content'))
            binary += getContainerContentBytes(elem)
    
    return binary

# Test code: Recompile call headers
parser = argparse.ArgumentParser(description=f'recompile an XML exported from RadioDatTools.py. Usage: script.py <input.xml> [output.bin]')
parser.add_argument('input', type=str, help="Input XML to be recompiled.")
parser.add_argument('output', nargs="?", type=str, help="Output Filename (.bin). If not present, will re-use basename of input with -mod.bin")
parser.add_argument('-x', '--hex', action='store_true', help="Outputs hex with original subtitle hex, rather than converting dialogue to hex.")

def main():
    global subUseOriginalHex 
    args = parser.parse_args()

    # Read new radio source
    radioSource = ET.parse(args.input)

    if args.output:
        outputFilename = args.output
    else:
        outputFilename = args.input.split("/")[-1].split(".")[0] + '-mod.bin'

    if args.hex:
        subUseOriginalHex = True

    root = radioSource.getroot()

    outputContent = b''
    for call in root:
        attrs = call.attrib
        outputContent += bytes.fromhex(attrs.get("content"))
        for subelem in call:
            outputContent += handleElement(subelem)
        outputContent += b'\x00'
        if attrs.get('graphicsBytes') is not None:
            outputContent += bytes.fromhex(attrs.get('graphicsBytes'))
        # print(content)

    f = open(outputFilename, 'wb')
    f.write(outputContent)
    f.close()

if __name__ == '__main__':
    main()