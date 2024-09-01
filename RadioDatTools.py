#!/bin/python

"""

This is the main script. See bottom for command arguments and how we parse the command. 

- Project notes
- TODO: Remove handleUnknown() or replace with different logic.
- TODO: Add base64 hashing to determine input file 
- TODO: Handle other cases, fix natashas script breaking shit (Cases)
- TODO: Mei ling scripts fucked up # BETTER NOW!
- TODO: Work on recompiler

Completed stuff:
- Parses english and Japanese characters
- Multiple outputs: Headers only, Iseeva style json (Dialogue only), XML heirarchical format

"""

import os, struct
from datetime import datetime
import radioTools.radioDict as radioDict
import argparse
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from translate import Translator

### UNUSED ?
# import re # Not used?
# import base64 # We will eventually hash the files and verify they will run properly. 

# XML Globals
root = ET.Element("RadioData")
elementStack = [(root, -1)]

# Graphics data variable list
customGraphicsData = []

## Formatting Settings!

debugOutput = False
splitCalls = False
exportGraphics = False

translateToggle = False
translator = Translator(from_lang="ja", to_lang="en")

# Script variables 
offset = 0
radioData = b''
callDict = {}
fileSize = 0

# FILE OPERATIONS

# Debugging files:

def setRadioData(filename: str) -> bool:
    global radioData
    global fileSize
    global elementStack
    
    radioFile = open(filename, 'rb')
    radioData = radioFile.read()
    fileSize = len(radioData)
    elementStack = [(root, fileSize)]
    return True

def setOutputFile(filename: str) -> bool:
    global output
    current_time = datetime.now().strftime("%H%M%S")
    current_date = datetime.now().strftime("%Y-%m-%d") 
    output = open(f'{filename}-{current_date}-{current_time}.log', 'w')

def splitCall(offset: int, length: int) -> None:
    global radioData
    global fileSize
    end = offset + length
    if end > fileSize:
        splitCall = radioData[offset:fileSize]
    else:
        splitCall = radioData[offset:end]
    filename = 'extractedCallBins/' + str(offset) + '.bin'
    f = open(filename, 'wb')
    f.write(splitCall)
    f.close()

# Reference data

# A lot of this is work in progress or guessing from existing scripts
commandNamesEng = { 
    b'\x01':'SUBTITLE',
    b'\x02':'VOX_CUES', 
    b'\x03':'ANI_FACE', 
    b'\x04':'ADD_FREQ',
    b'\x05':'MEM_SAVE', 
    b'\x06':'MUS_CUES', 
    b'\x07':'ASK_USER', 
    b'\x08':'SAVEGAME',
    b'\x10':'IF_CHECK', 
    b'\x11':'ELSE', 
    b'\x12':'ELSE_IFS', 
    b'\x30':'RND_SWCH',
    b'\x31':'RND_OPTN', 
    b'\x40':'EVAL_CMD' 
    # 'THEN_DO'
}

freqList = [
    b'\x37\x05', # 140.85, Campbell
    b'\x37\x10', # 140.96, Mei Ling
    b'\x36\xbf', # 140.15, Meryl
    b'\x37\x20', # 141.12, Otacon
    b'\x37\x48', # 141.52, Nastasha
    b'\x37\x64', # 141.80, Miller
    b'\x36\xE0', # 140.48, Deepthroat
    b'\x36\xb7',  # 140.07, Staff, Integral exclusive
    b'\x36\xbb',
    bytes.fromhex('36bb'), 
    bytes.fromhex('36bc'), # 140.12, ????
    b'\x36\xbc', 
    b'\x37\xac', # 142.52, Nastasha? ACCIDENT
]

# Hashes for each radio file. I did not include Integral yet, as it won't suit the needs of this project. We'll need to write something to hash the files when ingested.
radioHashes = {
    "usa-d1":'9b6d223d8e1a9e562e2c188efa3e6425a87587f35c6bd1cfe62c5fa7ee9a0019',    # USA Disc 1
    "usa-d2":'e6cf1b353db0bc7620251b6916577527debfdd5bdcd125b3ca9ef5c9a0aef61e',    # USA Disc 2
    "jpn-d1":'f588fb57ce6c5754c39ca5ec9d52fe2c5766a2e51bcb0ea7a343490e0769c6b2',    # Japanese Disc 1 ## Premium package seems to match the retail
    "jpn-d2":'b46088c2c10e0552fcd6f248ea4fdf0bcf428691184dae053267f4d93f97cec9',    # Japanese Disc 2 
}

def getHash(): # Not yet implemented! 
    hash = radioHashes
    return hash

def commandToEnglish(hex: bytes) -> str:
    global output
    try: 
        commandNamesEng[hex]
        return commandNamesEng[hex]
    except:
        return f'BYTE {hex.hex()} WAS NOT DEFINED!!!!'

# Analysis commands

def checkFreq(offset: int) -> bool:  
    """ 
    Checks if the offset is the start of a codec call or not. 
    Returns True or False.
    """
    global radioData
    if radioData[offset:offset + 2] in freqList and radioData[offset + 8].to_bytes() == b'\x80':
        return True
    else: 
        return False
    
def getFreq(offset: int) -> float: # If freq is at offset, return frequency as 140.15
    global radioData

    freq = struct.unpack('>H', radioData[ offset : offset + 2])[0]
    return freq / 100

def getLength(offset: int) -> int: # Returns COMMAND length, offset must be at the 0xff bytes, length is bytes 1 and 2.
    global radioData
    
    lengthBytes = radioData[offset + 2: offset + 4]
    length = struct.unpack('>H', lengthBytes)[0]
    return length + 2

def getLengthManually(offset: int) -> int: # Assumes it's a header ending in 80 XX XX // FF starting the next block
    length = 0
    while True:
        length += 1
        if radioData[offset + length].to_bytes() == b'\xff' and radioData[offset + length - 3].to_bytes() == b'\x80' and not checkFreq(offset + length):
            return length
        """elif radioData[offset + length].to_bytes() == b'\xff' and radioData[offset + length - 1].to_bytes() == b'\x00' and radioData[offset + length + 1].to_bytes() in commandNamesEng:
            return length"""

def getCallLength(offset: int) -> int: # Returns CALL length, offset must be at the freq bytes
    global radioData

    lengthT = struct.unpack('>H', radioData[offset + 2 : offset + 4])[0]
    return lengthT

def handleCallHeader(offset: int) -> int: # Assume call is just an 8 byte header for now, then \x80, then script length (2x bytes)
    global radioData
    global output
    global root
    global elementStack
    global splitCalls

    # OPTIONAL Add an offset tracker output?
    
    header = 11 # Call headers are static 11
    line = radioData[ offset : offset + header ]

    # Separate the header
    humanFreq = getFreq(offset)
    unk0 = line[2:4] # face 1
    unk1 = line[4:6] # face 2
    unk2 = line[6:8] # Usually nulls
    length = struct.unpack('>H', line[9:11])[0] + 9 # Header - 2

    if splitCalls:
        splitCall(offset, length)
    # Quick error check11ing
    """if debugOutput:
        if line[8].to_bytes() != b'\x80':
            output.write(f'ERROR! AT byte {offset}!! \\x80 was not found \n') # This means what we analyzed was not a call header!
            return 1"""

    # Get graphics data and write to a global dict:
    global callDict 
    graphicsData = getGraphicsData(offset + length)
    if len(graphicsData) % 36 == 0:
        callDict = radioDict.makeCallDictionary(offset, graphicsData)
    else:
        print(f'Graphics parse error offset {offset}! \n')
    
    output.write(f'Call Header: {humanFreq:.2f}, offset = {offset}, length = {length}, UNK0 = {unk0.hex()}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, Content = {line.hex()}\n')

    call_element = ET.SubElement(root, "Call", {
        "offset": f'{offset}',
        "freq": f'{humanFreq}',
        "length": f'{length}', 
        "unknownVal1": unk0.hex(),
        "unknownVal2": unk1.hex(),
        "unknownVal3": unk2.hex(),
        "content": line.hex(),
        "graphicsBytes": graphicsData.hex()
        })
    
    checkElement(length)
    elementStack.append((call_element, length))

    return header

def handleUnknown(offset: int) -> int: # Iterates checking frequency until we get one that is valid.... hopefully this gets us past a chunk of unknown data.
    """
    Assuming at this point that this is graphics data. Graphics data is always evenly divisble by 36 bytes. 
    Each grouping of 36 bytes creates a TGA image file. These can be output to individual files using the 
    RadioDict module.
    """
    count = 0
    global fileSize
    global exportGraphics
    while True:
        if offset + count == fileSize:
            break
        elif checkFreq(offset + count): # Why the +1 ?
            break
            """elif radioData[offset + count].to_bytes() == b'\xff' and radioData[offset + count + 1].to_bytes() in commandNamesEng:
            break"""
        else: 
            count += 1
    content = radioData[offset: offset + count]
    
    if len(content) % 36 != 0: # Alert user if the graphics content not evenly divisible by 36 bytes
        output.write(f'ERROR! Unknown block at offset {offset}! ')

    output.write(f'Unknown block: {content.hex()}')
    output.write('\n')
    return count

def handleCommand(offset: int) -> int: # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    """
    TERMINOLOGY:
    length  = length of the entire container (including header and subcontainers)
    header = header length
    line = Usually their header text/content
    """
    global output
    global root
    global elementStack

    # 0x31 does not have FF, we assume we're at the FF unless we see a 0x31!
    if radioData[offset].to_bytes() == b'\x31':
        commandByte = b'\x31'
    else:
        commandByte = radioData[offset + 1].to_bytes()
    
    output.write(f"{commandToEnglish(commandByte)} -- ")

    # We now deal with the byte
    match commandByte:

        case b'\x00': # This should no longer occur.
            print(f'Error at {offset}! A null command was found.')
        
        case b'\x01':
            length = getLength(offset) 
            line = radioData[ offset : offset + length]
            # Don't do logic for extra nulls, caught in main loop.
            face = line[4:6]
            anim = line[6:8]
            unk3 = line[8:10]
            dialogue = line[10 : length]
            dialogueHex = dialogue.hex()
            
            lineBreakRepace = False
            if b'\x80\x23\x80\x4e' in dialogue:  # this replaces the in-game hex for new line with a \\r\\n
                lineBreakRepace = True
                dialogue = dialogue.replace(b'\x80\x23\x80\x4e', b'\x5c\x72\x5c\x6e')

            # Translate
            translatedDialogue = translateJapaneseHex(dialogue) # We'll translate when its working
            dialogue = str(translatedDialogue)
            translatedDifference = len(dialogue) - len(translatedDialogue)

            if translateToggle:
                dialogue = translator.translate(dialogue)
                print(f'Translated offset {offset}: {dialogue}')

            # Output to text file
            output.write(f'Offset = {offset}, Length = {length}, FACE = {face.hex()}, ANIM = {anim.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, \tText: {(dialogue)}\n')
            
            subtitle_element = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                'face': face.hex(),
                "anim": anim.hex(),
                "unk3": unk3.hex(),
                "text": dialogue,
                "textHex":  dialogueHex,
                "lengthLost": str(translatedDifference)
            })

            return length
        
        case b'\x02':
            header = getLengthManually(offset)
            length = getLength(offset)
            line = radioData[offset : offset + header]
            voxLength1 = struct.unpack('>H',line[2:4])[0]
            voxLength2 = struct.unpack('>H',line[9:11])[0]
            containerLength = voxLength2 - 3
            
            # Check for even length numbers
            if debugOutput:
                if voxLength1 - voxLength2 != 7:
                    print(f'ERROR!! OFFSET {offset} HAS A 0x02 that does not evenly fit!')

            voxElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(voxLength1),
                "header": str(header),
                "containerLength": str(containerLength),
                "content": f'{line.hex()}'
            })
            checkElement(length)
            elementStack.append((voxElement, length))
            output.write(f'Offset: {str(offset)}, LengthA = {voxLength1}, LengthB = {voxLength2}, Content: {str(line.hex())}\n')
            
            return header
        
        case b'\x03':
            length = getLength(offset)
            header = 10 # Should be static
            line = radioData[offset : offset + length]
            containerLength = line[2:4]
            face = line[4:6]
            anim = line[6:8]
            buff = line[8:10]

            Anim_Element = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "header": str(header),
                'face': line[4:6].hex(),
                'anim': line[6:8].hex(),
                'buff': line[8:10].hex(),
                'content': line.hex()
            })

            output.write(f'Offset: {str(offset)}, length = {length} FACE = {face.hex()}, ANIM = {anim.hex()}, content: {str(line.hex())}\n')
            return length
        
        case b'\x04':
            length = getLength(offset)
            line = radioData[offset : offset + length]
            containerLength = getLength(offset)
            freq = getFreq(offset + 4)
            entryName = line[6 : length]
            entryNameStr = translateJapaneseHex(entryName)

            # Just a safety since the length of this was hard-coded
            if debugOutput:
                if struct.unpack('>H', line[2:4])[0] != length - 2:
                    print(f'ERROR! Offset {offset} has an ADD_FREQ op that does not match its length!')

            SaveFreqElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "freq": str(freq),
                "name": entryNameStr,
                "content": line.hex()
            })

            output.write(f'Offset: {str(offset)}, length = {containerLength}, freqToAdd = {freq}, entryName = {entryName}, FullContent: {str(line.hex())}\n')
            return length
        
        case b'\x05':
            # Content (USA specific): b'ff050565120000aa07098044806f8063806b0007098263828f8283828b00071180488065806c80698070806f8072807400071182678285828c82898290828f8292829400071780548061806e806b900180488061806e80678061807200071782738281828e828b814082678281828e82878281829200070980438065806c806c00070982628285828c828c000713804d80658064806990018072806f806f806d000713826c82858284828981408292828f828f828d00070d80418072806d806f8072807900070d82608292828d828f8292829900071580418072806d806f80728079900180538074806800071582608292828d828f82928299814082728294828800070d80438061806e8079806f806e00070d82628281828e8299828f828e000717804e8075806b806590018042806c8064806790018031000717826d8295828b828581408261828c828482878140825000071b804e8075806b806590018042806c80648067802e90018042803100071b826d8295828b828581408261828c8284828781448140826182500007178043806d806e80648065807290018072806f806f806d0007178262828d828e82848285829281408292828f828f828d00071b804e8075806b806590018042806c80648067802e90018042803200071b826d8295828b828581408261828c828482878144814082618251000707804c80618062000707826b82818282000709804380618076806500070982628281829682850007198055802e80478072806e80649001805080738073806780650007198274814482668292828e82848140826f82938293828782850007158043806f806d806d9001805480778072900180410007158262828f828d828d81408273829782928140826000071b8052806f806f806690168043806f806d806d900180548077807200071b8271828f828f8286815e8262828f828d828d81408273829782920007158043806f806d806d9001805480778072900180420007158262828f828d828d814082738297829281408261000715805480778072900180578061806c806c90018041000715827382978292814082768281828c828c8140826000070f80578061806c806b80778061807900070f82768281828c828b8297828182990007138053806e806f8077806680698065806c80640007138272828e828f8297828682898285828c828400071b8042806c8061807380749001804680758072806e80618063806500071b8261828c8281829382948140826582958292828e8281828382850007178043806180728067806f90018045806c80658076802e0007178262828182928287828f81408264828c82858296814400071380578061807280658068806f80758073806500071382768281829282858288828f82958293828500071b80578061807280658068806f8075807380659001804e8074806800071b82768281829282858288828f8295829382858140826d8294828800071b8055802e80478072806e8064900180428061807380659001803100071b8274814482668292828e8284814082618281829382858140825000071b8055802e80478072806e8064900180428061807380659001803200071b8274814482668292828e8284814082618281829382858140825100071b8055802e80478072806e8064900180428061807380659001803300071b8274814482668292828e828481408261828182938285814082520007138043806d806e806490018072806f806f806d0007138262828d828e828481408292828f828f828d000715805380708070806c80799001805280748065802e000715827282908290828c82998140827182948285814400071380458073806390018052806f80758074806500071382648293828381408271828f829582948285000000'
            length = getLength(offset) # Might be US specific?
            line = radioData[offset:offset + length]
            output.write(f' -- Offset: {str(offset)}, length = {length}, FullContent: {str(line.hex())}\n')

            SaveCommand = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "content": line.hex(),
            })
            return length

        case b'\x06' | b'\x07' | b'\x08': 
            length = getLength(offset)
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')

            cuesElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "content": line.hex(),
            })
            return length

        case b'\x10': # 
            length = getLength(offset)
            header = getLengthManually(offset) # Maybe not ?
            line = radioData[offset : offset + header] # - 4 because from the offset we read the 3rd and 4th bytes. 
            lengthInner = struct.unpack('>H', line[header - 2 : header])[0] - 2  # We were preivously calculating length wrong, this is correct for the container
            
            """ # Former troubleshooting exports
            lengthA = getLength(offset)
            lengthB = getLength(offset + header - 4) + header
            lABytes = radioData[offset + 2: offset + 4]
            lBBytes = radioData[offset + header - 2: offset + header]
            if lengthA == lengthB - 3:
                print(f'FF10 at offset {offset} length matched!')
            else:
                print(f'FF10 at offset {offset} length WAS NOT MATCHED!!! A: {lengthA}, {lABytes.hex()} B: {lengthB}, {lBBytes.hex()}')
                """

            """output.write(f'Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            """

            ifElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "header": str(header),
                "containerLength": str(length),
                "content": line.hex(),
            })

            checkElement(length)
            elementStack.append((ifElement, length))

            doElement = ET.SubElement(elementStack[-1][0], "THEN_DO", {
                "offset": str(offset + header),
                "length": str(lengthInner),
            })

            checkElement(header + lengthInner)
            elementStack.append((doElement, lengthInner))

            return header
        
        case b'\x11': # Else respectively
            header = 5 # Maybe not ?
            line = radioData[offset : offset + header]
            length = header + struct.unpack('>H', line[header - 2 : header])[0] - 2 # We were preivously calculating length wrong, this is correct for the container
            output.write(f' -- Offset = {offset}, header = {header}, length = {length} Content = {line.hex()}\n')

            conditionalElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "containerLength": str(length - header),
                "content": line.hex(),
            })

            checkElement(length)
            elementStack.append((conditionalElement, length))

            return header
        
        case b'\x12': # Elseif
            header = getLengthManually(offset) # Maybe not ?
            line = radioData[offset : offset + header]
            length = header + struct.unpack('>H', line[header - 2 : header])[0] - 2 # We were preivously calculating length wrong, this is correct for the container
            containerLength = struct.unpack(">H", line[-2:len(line)])[0] - 3
            containerLength = header + struct.unpack('>H', line[header - 2 : header])[0] - 3
            output.write(f' -- Offset = {offset}, header = {header}, length = {length} Content = {line.hex()}\n')

            conditionalElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "containerLength": str(containerLength),
                "content": line.hex(),
            })

            checkElement(length)
            elementStack.append((conditionalElement, length))

            return header
        
        case b'\x30':
            # 30 is handled different, as it has a container header
            length = getLength(offset)
            header = 6
            line = radioData[offset : offset + header]

            randomElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), 
                {
                    "offset": str(offset),
                    "headerLength": str(header),
                    "length": str(length),
                    "content": line.hex()
                }
            )
            checkElement(length)
            elementStack.append((randomElement, length))

            return header 
        
        case b'\x31':
            # 31 passes offset as one before to match the command byte:
            header = 6
            line = radioData[offset : offset + header]
            length = struct.unpack('>H', line[4 : 6])[0] + 4

            randomElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), 
                {
                    "offset": str(offset),
                    "headerLength": str(header),
                    "length": str(length),
                    "content": line.hex()
                }
            )
            checkElement(length)
            elementStack.append((randomElement, length))
            return header
        
        case b'\x40':
            # The last bytes in the 0x40 expression are 14 31 00...
            length = 16
            while True:
                checkingOffset = offset + length
                if checkFreq(checkingOffset):
                    break

                if radioData[checkingOffset].to_bytes() == b'\xff' or b'\x00':
                    if radioData[checkingOffset - 3:checkingOffset] == b'\x14\x31\x00':
                        break
                
                length += 1
            
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            
            randomElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "content": line.hex()
            })
            return length
        
        # case b'\xFF': # This basically menas offset should be 1 less... we'll continue processing but output will error at this offset.
            output.write(f'ERROR! Command was 0xFF at offset {offset}!!! \n')
            if debugOutput:
                print(f'ERROR! Command was 0xFF at offset {offset}!!! \n')
            length = 1
            return length

        # case _:
            output.write(f'ERROR! Command is not yet cased! Command = {commandByte} -- ')
            
            length = getLengthManually(offset)
            line = radioData[offset : offset + length]
            output.write(f'Offset: {offset}, Content = {line.hex()}\n')
            return length

def getGraphicsData(offset: int) -> bytes: # This is a copy of handleUnknown, but we return the string and hope its the graphics data 
    """
    copied from handleUnknown() but we return the bytestring of the graphics data
    """
    count = 0
    global fileSize
    global exportGraphics
    global call_element
    while True:
        if offset + count >= fileSize - 1:
            break
        elif checkFreq(offset + count): # Why the +1 ?
            break
        elif radioData[offset + count].to_bytes() == b'\xff' and radioData[offset + count + 1].to_bytes() in commandNamesEng:
            break
        else: 
            count += 36
    content = radioData[offset: offset + count]

    return content

def checkElement(length):
    """
    Pops the top element off the stack (if its longer than 1)
    Removes the last amount of length from it
    If there is still length remaining, we add it back to the stack.
    """
    if len(elementStack) > 0:
        current_element, current_length = elementStack.pop()
        newElementLength = current_length - length
        if newElementLength > 0:
            elementStack.append((current_element, newElementLength))
            
## Translation Commands:
def translateJapaneseHex(bytestring: bytes) -> str: # Needs fixins, maybe move to separate file?
    global callDict
    return radioDict.translateJapaneseHex(bytestring, callDict)

"""def extractRadioCallHeaders(outputFilename: str) -> None:
    offset = 0
    global debugOutput
    global fileSize
    
    setOutputFile(outputFilename)

    # Handle inputting radio file:
    global radioData

    while offset < fileSize - 1: # We might need to change this to Case When... as well.
        # Offset Tracking
        if debugOutput:
            print(f'offset is {offset}')

        # MAIN LOGIC
        if radioData[offset].to_bytes() == b'\x00': # Add logic to tally the nulls for reading ease
            length = 1
        elif checkFreq(offset):
            handleCallHeader(offset) 
            length = 11
        else:
            length = 1
        offset += length
        if offset == fileSize:
            print(f'File was parsed successfully! Written to {outputFilename}')
            break
    
    print(f'File was parsed successfully! Written to {outputFilename}')
    output.close()"""

def analyzeRadioFile(outputFilename: str) -> None: # Cant decide on a good name, but this outputs a readable text file with the information broken down.
    offset = 0
    global debugOutput
    global radioData
    global fileSize
    global output
    
    setOutputFile(outputFilename)

    while offset < fileSize: # We might need to change this to Case When... as well.
        # Offset Tracking
        if debugOutput:
            print(f'Main loop: offset is {offset}')

        # MAIN LOGIC
        if radioData[offset].to_bytes() in [b'\xFF', b'\x31']: # Commands start with FF
            length = handleCommand(offset)
        elif checkFreq(offset):
                length = handleCallHeader(offset)
        elif radioData[offset].to_bytes() == b'\x00':
            if elementStack[-1][1] == 1:
                length = 1
            elif offset == fileSize - 1:
                length = 1
            elif radioData[offset + 1].to_bytes() in [b'\xFF', b'\x31']:
                length = 1
            elif checkFreq(offset + 1):
                length = 1
            """elif elementStack[-1][1] == 1:
                length = 1
                output.write(f'WE HANDLED A NULL AND WE DONT KNOW WHY!\n')"""
        elif len(elementStack) == 1 and not checkFreq(offset):
                length = handleUnknown(offset)
        # TEMPORARY SHIFT TO SEE IF WE FIXED THIS
        else: # Something went wrong, we need to kinda reset
            print(f'Something went wrong, we need to kinda reset. Offset = {offset}')
            length = handleUnknown(offset) # This will go until we find a call frequency
        
        checkStack = len(elementStack)
        if offset < fileSize - 2: # Temp fix for the logic at end of the file.
            if radioData[offset + 1].to_bytes() != b'\x10':
                checkElement(length)
        if radioData[offset] == b'\x00' and checkStack == len(elementStack): # If we handled a null and it did NOT remove an element:
            output.write(f"Null! (Main loop) offset = {offset}\n")
            nullElement = ET.SubElement(elementStack[-1][0], "Null", {"Offset": f'{offset}', "length": "1"})
        
        # Add length to offset for next loop
        offset += length

    output.close()

    if offset >= fileSize - 1:
        print(f'File was parsed successfully! Written to {outputFilename}')

# This doesn't work because i did not code with contextual variables in mind >:O
if __name__ == '__main__':
    """
    This will parse arguments and run both headers extract and full analysis. 
    Output is now "[input filename]-output" unless otherwise specified
    """
    # Backup variables
    filename = 'RADIO.DAT'
    outputFilename = 'Radio-decrypted.txt'
    
    # We should get args from user. Using argParse
    parser = argparse.ArgumentParser(description=f'Parse a binary file for Codec call GCL. Ex. script.py <filename> [output.txt] -?')

    # REQUIRED
    parser.add_argument('filename', type=str, help="The call file to parse. Can be RADIO.DAT or a portion of it.")
    # Optionals
    parser.add_argument('output', nargs="?", type=str, help="Output Filename (.txt)")
    parser.add_argument('-v', '--verbose', action='store_true', help="Write any errors to stdout for help parsing the file")
    parser.add_argument('-j', '--japanese', action='store_true', help="Toggles translation for Japanese text strings") # Remove later when issue with english resolved
    parser.add_argument('-s', '--split', action='store_true', help="Split calls into individual bin files")
    parser.add_argument('-H', '--headers', action='store_true', help="Extract call headers ONLY!")
    parser.add_argument('-g', '--graphics', action='store_true', help="export graphics")
    parser.add_argument('-x', '--xmloutput', action='store_true', help="Exports the call data into XML format")
    parser.add_argument('-z', '--iseeeva', action='store_true', help="Exports the dialogue in a json like Iseeeva's script")
    parser.add_argument('-S', '--silent', action='store_true', help="Silent / no output message when done.")

    args = parser.parse_args()

    # Set input filename
    filename = args.filename
    baseFilename = filename.split("/")[-1]
    baseFilename = baseFilename.split(".")[0]

    # Set output Filename
    if args.output:
        outputFilename = f'{args.output}'
    else:
        outputFilename = f'{baseFilename}-output'

    if args.verbose:
        debugOutput = True
    
    if args.split:
        splitCalls = True
        os.makedirs('extractedCallBins', exist_ok=True)
    
    if args.graphics:
        exportGraphics = True

    if args.japanese:
        translateToggle = True
    
    setRadioData(filename)
    radioDict.openRadioFile(filename)
        
    if args.graphics:
        exportGraphics = True
    
    analyzeRadioFile(outputFilename)

    fancy = True # For now this is the only way to properly output the file. 
    # Optional print the string: 
    if args.xmloutput:
        if fancy:
            xmlstr = parseString(ET.tostring(root)).toprettyxml(indent="  ")
            xmlFile = open(f'{outputFilename}.xml', 'w')
            xmlFile.write(xmlstr)
            xmlFile.close()
        else:
            # THE OLD METHOD! 
            xmlOut = ET.ElementTree(root)
            xmlOut.write(f"{outputFilename}.xml")
    
    if args.headers:
        headerRoot = ET.Element("RadioHeaders")
        for call in root.findall(f'.//Call'):
            call_element = ET.Element("Call")
        
            # Copy attributes from the original Call element
            for attr, value in call.attrib.items():
                call_element.set(attr, value)
            headerRoot.append(call_element)
   
        headerFile = open(f'{outputFilename}-headers.xml', 'w')
        xmlstr = parseString(ET.tostring(headerRoot)).toprettyxml(indent="  ")
        headerFile.write(xmlstr)
        headerFile.close()
    
    if args.iseeeva:
        import json
        dialogueData = {}
        for call in root.findall(f'.//Call'):
            callOffset = call.attrib.get('Offset')
            callText = {}
            for subs in call.findall(f'.//SUBTITLE'):
                offset = subs.attrib.get('offset')
                text = subs.attrib.get('text')
                callText[int(offset)] = text
                dialogueData[int(callOffset)] = callText
        
        with open(f"{outputFilename}-Iseeva.json", 'w') as f:
            json.dump(dialogueData, f, ensure_ascii=False, indent=2)
    
    if args.graphics:
        with open("graphicsExport/GraphicsFound.txt", 'w') as f:
            f.write(f'=================================\n')
            f.write(f"{filename} has these graphics that were unmatched:\n")
            num = 0
            unidentifiedGraphicsLocal = []
            for item in radioDict.unidentifiedGraphics:
                if item not in unidentifiedGraphicsLocal:
                    unidentifiedGraphicsLocal.append(item)
            for item in unidentifiedGraphicsLocal:
                num += 1
                f.write(str(item))
                newFile = f'{outputFilename}-{num}'
                radioDict.outputGraphic(newFile, bytes.fromhex(item))
                f.write('\n')
            f.close()