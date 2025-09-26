"""
Recompiler for MGS RADIO.DAT files. This requires exported Radio XML and .json files created by RadioDatTools.py

Steps to use for translation:

1. Export XML and Json from RadioDatTools from source disk RADIO.DAT
2. Adjust dialogue in the .json file.
3. Run script with both files as arguments. 

We will output to RADIO.DAT or optionally a filename of your choice. 

To do list:
TODO: ~~Element checker~~ I think this is done
TODO: Need logic to re-insert b'\x80' before each punctuation mark that needs it (new lines and japanese supertext pairs {a, b})
TODO: Calculate double byte length characters for length in subtitles

"""

stageBytes: bytearray = b''
debug = False

# ==== Dependencies ==== #

import os, struct
import argparse
import xml.etree.ElementTree as ET
import StageDirTools.callsInStageDirFinder as stageTools
import translation.radioDict as RD
import xmlModifierTools as xmlFix

# Debugging for testing calls recompile with correct info
subUseOriginalHex = False
encodeJapaneseChars = False
useDWidSaveB = False

newOffsets = {}
stageDirFilename = 'radioDatFiles/STAGE-jpn-d1.DIR'

# ==== DEFS ==== #

# Large steps here
def realignOffsets():
    print(f'Offset integrity reviewed and done')

def createBinary(filename: str, binaryData: bytes):
    with open(filename, 'wb') as f:
        f.write(binaryData)
        f.close
    print(f'Binary data created: {filename}, size: {len(binaryData)}!')

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

    WE DO NOT ADJUST LENGTH HERE!
    """
    global subUseOriginalHex
    global encodeJapaneseChars

    attrs = subtitle.attrib
    subtitleBytes = bytes.fromhex('ff01')
    lengthBytes = struct.pack('>H', int(attrs.get("length")) - 2) # TODO: Check this is equal to what we intend!
    face = bytes.fromhex(attrs.get("face"))
    anim = bytes.fromhex(attrs.get("anim"))
    unk3 = bytes.fromhex(attrs.get("unk3"))

    text = attrs.get("text").encode('utf-8')
    if "newTextHex" in attrs.keys():
        text = bytes.fromhex(attrs.get('newTextHex'))
    # textBytes = codecs.decode(attrs.get("text"), 'unicode_escape')
    text = text.replace(bytes.fromhex('5c725c6e'), bytes.fromhex('8023804e')) # Replace \r\n with in-game byte codes for new lines
    
    if subUseOriginalHex:
        subtitleBytes = subtitleBytes + lengthBytes + face + anim + unk3 + bytes.fromhex(attrs.get('textHex'))
    elif encodeJapaneseChars:
        subtitleBytes = subtitleBytes + lengthBytes + face + anim + unk3 + RD.encodeJapaneseHex(attrs.get("text"), None, useDoubleLength=False)[0] + bytes.fromhex('00')
    else:
        subtitleBytes = subtitleBytes + lengthBytes + face + anim + unk3 + text + bytes.fromhex('00')
        
    return subtitleBytes

def getVoxBytes(vox: ET.Element) -> bytes:
    """
    Returns the hex for a VOX container (FF02). 
    Because it is a container that contains Subtitle elements, we will compile that hex here.
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
        elemBytes = elemBytes + struct.pack('>H', length) + freq + name + b'\x00'
    
    return elemBytes

def getContentBytes(elem: ET.Element) -> bytes: 
    """
    This one is to get binary when we specifically mark a 'content' field. Full list of what this works for:
    FF04, FF06, FF08
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

def getAddFreq(elem: ET.Element) -> bytes:
    """
    This is for FF04, add contact to codec mem. 
    Content/length should be fixed earlier. 
    """
    binary = b''
    content = elem.get('content') + elem.get('name') + "00"
    binary += content.hex()

    return binary

def getGoblinBytes(elem: ET.Element) -> bytes:
    """
    For the innards of the Prompt user and Save Block data
    """
    global subUseOriginalHex
    global useDWidSaveB

    binary = b''
    if elem.tag ==  'USR_OPTN':
        content = "07" + int(elem.get('length')).to_bytes().hex() + elem.get('text').encode('utf8').hex() + "00"
        binary = bytes.fromhex(content)
        if bytes.fromhex("2E") in binary:
            period = binary.find(bytes.fromhex("2e"))
            binary = binary[0 : period - 1] + bytes.fromhex("80") + binary[period - 1:] # TODO: NEEDS TESTING
    elif elem.tag ==  'SAVE_OPT':
        if useDWidSaveB or subUseOriginalHex:
            contentA = RD.encodeJapaneseHex(elem.get('contentA'), "", useDoubleLength=True)[0] # DOES THIS WITH THE FLAG NOW
            """if bytes.fromhex("2E") in binary:
                period = contentA.find(bytes.fromhex("2e"))
                contentA = contentA[0 : period] + bytes.fromhex("80") + contentA[period:] # TODO: NEEDS TESTING"""
        else:
            contentA = RD.encodeJapaneseHex(elem.get('contentA'), "", useDoubleLength=False)[0]
        contentB = elem.get('contentB').encode("shift-jis")
        binary = bytes.fromhex("07") + (len(contentA) + 1).to_bytes() + contentA + bytes.fromhex("00")
        binary = binary + bytes.fromhex("07") + (len(contentB) + 1).to_bytes() + elem.get('contentB').encode("shift-jis") + bytes.fromhex("00")
    else:
        print(f'WE GOT THE WRONG ELEMENT! Should be goblin, got {elem.text}')
    
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
            """case 'ADD_FREQ':
            binary = getFreqAddBytes(elem)"""
        case 'ANI_FACE' | 'MUS_CUES' | 'SAVEGAME' | 'EVAL_CMD' | 'ADD_FREQ':  # ADD_FREQ temp as a check since we set the content.
            # ff03-08, FF40
            binary = getContentBytes(elem)
        case 'USR_OPTN' | 'SAVE_OPT':
            binary = getGoblinBytes(elem)
        case 'IF_CHECK' | 'ELSE' | 'ELSE_IFS' | 'RND_SWCH' | 'RND_OPTN' | 'MEM_SAVE' | 'ASK_USER': 
            binary = bytes.fromhex(attrs.get('content'))
            binary += getContainerContentBytes(elem)
            # Troubleshooting
            """print(attrs.get('length'))
            print(len(binary))"""
        case 'THEN_DO': 
            binary += getContainerContentBytes(elem)
    
    return binary

def fixStageDirOffsets():
    """
    Takes the finalized offset dict and uses the new values to overwrite values in stage.dir. 
    Make sure you've backed up the original stage.dir file!
    """
    global stageBytes 
    global newOffsets
    global debug

    for key in stageTools.offsetDict.keys():
        # We can move forward if there's a match. Might skip the initial few.
        stageOffset = int(stageTools.offsetDict.get(key)[0])
        newOffset = newOffsets.get(stageOffset)
        if newOffset == stageOffset:
            if debug:
                print(f'{newOffset} = {stageOffset}')
            continue
        elif newOffset == None:
            print(f'ERROR! Offset invalid! Key: {key} returned {stageTools.offsetDict.get(key)}')
            continue

        newOffsetHex = struct.pack('>L', newOffset)
        stageBytes[key + 5: key + 8] = newOffsetHex[1:4]
        if debug:
            print(newOffsetHex.hex())
            print(stageBytes[key: key + 8].hex())

def main(args=None):
    global subUseOriginalHex 
    global encodeJapaneseChars
    global stageBytes
    global debug
    global useDWidSaveB
    
    
    if args == None:
        args = parser.parse_args()

    # Read new radio source
    if args.prepare:
        print(f'Preparing XML by repairing lengths...')
        root = xmlFix.init(args.input)
    else:
        radioSource = ET.parse(args.input)
        root = radioSource.getroot()
    
    if args.reencode:
        encodeJapaneseChars = True

    if args.output:
        outputFilename = args.output
    else:
        outputFilename = 'new-' + args.input.split("/")[-1].split(".")[0] + '.bin'

    if args.hex:
        subUseOriginalHex = True
        xmlFix.subUseOriginalHex = True
        
    if args.double:
        useDWidSaveB = True
        xmlFix.useDWSB = True
    
    if args.debug:
        debug = True
        xmlFix.debug = True
        RD.debug = True

    outputContent = b''

    for call in root:
        # Record the new offset created for the call
        newCallOffset = len(outputContent)
        newOffsets.update({int(call.attrib.get("offset")): newCallOffset})

        # We put the call together, starting with the call header. 
        attrs = call.attrib
        outputContent += bytes.fromhex(attrs.get("content"))
        
        # Experimental change! This *should* make modified calls inject, while unmodified ones 
        if attrs.get('modified') == "true":
            subUseOriginalHex = True
            xmlFix.subUseOriginalHex = True
        else:
            subUseOriginalHex = False
            xmlFix.subUseOriginalHex = False

        for subelem in call:
            outputContent += handleElement(subelem)
        outputContent += b'\x00'
        if attrs.get('graphicsBytes') is not None and subUseOriginalHex == True: # 2nd change, inject graphics ONLY if using original hex.
            outputContent += bytes.fromhex(attrs.get('graphicsBytes'))
        # print(content)
    
    radioOut = open(outputFilename, 'wb')
    radioOut.write(outputContent)
    radioOut.close()

    if args.stageOut:
        stageOutFile = args.stageOut
    else:
        stageOutFile = 'new-STAGE.DIR'
    
    if args.stage:
        stageDirFilename = args.stage
        stageTools.init(stageDirFilename)
        stageBytes = bytearray(stageTools.stageData)
        fixStageDirOffsets()
        stageOut = open(stageOutFile, 'wb')
        stageOut.write(stageBytes)
        stageOut.close()

    if debug:
        print(newOffsets)

if __name__ == '__main__':
    # Parse arguments here, then run main so that this can be called from another parent script.
    parser = argparse.ArgumentParser(description=f'recompile an XML exported from RadioDatTools.py. Usage: script.py <input.xml> [output.bin]')
    parser.add_argument('input', type=str, help="Input XML to be recompiled.")
    parser.add_argument('output', nargs="?", type=str, help="Output Filename (.bin). If not present, will re-use basename of input with -mod.bin")
    parser.add_argument('-s', '--stage', nargs="?", type=str, help="Toggles STAGE.DIR modification, requires filename. Use -S for output filename.")
    parser.add_argument('-p', '--prepare', action='store_true', help="Run the text encoder and recompute lengths")
    parser.add_argument('-x', '--hex', action='store_true', help="Outputs hex with original subtitle hex, rather than converting dialogue to hex.")
    parser.add_argument('-v', '--debug', action='store_true', help="Prints debug information for troubleshooting compilation.")
    parser.add_argument('-D', '--double', action='store_true', help="Save blocks use double-width encoding [original vers.]")
    parser.add_argument('-R', '--reencode', action='store_true', help="Re-encode the characters based on characters.py (for non-english characters)")
    parser.add_argument('-S', '--stageOut', nargs="?", type=str, help="Output for new STAGE.DIR file. Optional.")
    
    main()