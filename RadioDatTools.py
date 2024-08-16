#!/bin/python

"""

This is the main script. See bottom for command arguments and how we parse the command. 

- Project notes
- TODO: Fix -j flag or remove entirely? Might be easier to just remove.
- TODO: Add base64 hashing to determine input file 
- TODO: Handle other cases, fix natashas script breaking shit (Cases)
- TODO: Mei ling scripts fucked up
- TODO: work on recompiler

Completed stuff:
- Parses english and Japanese characters
- Multiple outputs: Text (indented), Headers only, Iseeva style json (Dialogue only), XML heirarchical format



"""

import os, struct
import radioDict 
import argparse
import xml.etree.ElementTree as ET

### UNUSED ?
# import re # Not used?
# import base64 # We will eventually hash the files and verify they will run properly. 

# XML Globals
root = ET.Element("RadioData")
elementStack = [(root, -1)]

# Graphics data variable list
customGraphicsData = []

## Formatting Settings!

jpn = True # For now, lock to True until bug parsing in english is resolved. 
indentToggle = True
debugOutput = False
splitCalls = False
exportGraphics = False

# Script variables 
offset = 0
layerNum = 0
radioData = b''
callDict = {}
fileSize = 0

# FILE OPERATIONS

# Debugging files:

def setRadioData(filename: str) -> bool:
    global radioData
    global fileSize
    
    radioFile = open(filename, 'rb')
    radioData = radioFile.read()
    fileSize = len(radioData)
    return True

def setOutputFile(filename: str) -> bool:
    global output
    output = open(f'{filename}.txt', 'w')

def splitCall(offset: int, length: int) -> None:
    global radioData
    splitCall = radioData[offset:offset+length]
    filename = 'extractedCallBins/' + str(offset) + '.bin'
    f = open(filename, 'wb')
    f.write(splitCall)
    f.close()

# Reference data

# A lot of this is work in progress or guessing from existing scripts
commandNamesEng = { b'\x01':'SUBTITLE',
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
                    b'\x30':'SWITCH',
                    b'\x31':'SWITCHOP', 
                    b'\x40':'EVAL_CMD' 
}

freqList = [
    b'\x37\x05', # 140.85, Campbell
    b'\x37\x10', # 140.96, Mei Ling
    b'\x36\xbf', # 140.15, Meryl
    b'\x36\xb7', # 141.12, Otacon
    b'\x37\x48', # 141.52, Natasha
    b'\x37\xac', # 142.52, Natasha ACCIDENT
    b'\x37\x64', # 141.80, Miller
    b'\x36\xE0', # 140.48, Deepthroat
    b'\x36\xb7'  # 140.07, Staff, Integral exclusive
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
    
def indentLines() -> None: # Purely formatting help
    if indentToggle == True:
        for x in range(layerNum):
            output.write('\t')

# Analysis commands

def checkFreq(offset: int) -> bool:  # Checks if the next two bytes are a codec number or not. Returns True or False.
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

def getLengthManually(offset: int) -> int: # Assumes it's a header ending in 80 XX XX 
    length = 0
    while True:
        length += 1
        if radioData[offset + length].to_bytes() == b'\xff' and radioData[offset + length - 3].to_bytes() == b'\x80' and not checkFreq(offset + length):
            return length
        elif radioData[offset + length].to_bytes() == b'\xff' and radioData[offset + length - 1].to_bytes() == b'\x00' and radioData[offset + length + 1].to_bytes() in commandNamesEng:
            return length

def getCallLength(offset: int) -> int: # Returns CALL length, offset must be at the freq bytes
    global radioData

    lengthT = struct.unpack('>H', radioData[offset + 2 : offset + 4])[0]
    return lengthT

def handleCallHeader(offset: int) -> int: # Assume call is just an 8 byte header for now, then \x80, then script length (2x bytes)
    global radioData
    global output
    global layerNum
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
    
    call_element = ET.SubElement(root, "Call", {
        "Offset": f'{offset}',
        "Freq": f'{humanFreq}',
        "Length": f'{length}', 
        "UnknownVal1": unk0.hex(),
        "UnknownVal2": unk1.hex(),
        "UnknownVal3": unk2.hex(),
        })
    elementStack.append((call_element, length))

    # Get graphics data and write to a global dict:
    global callDict 
    graphicsData = getGraphicsData(offset + length)
    if len(graphicsData) % 36 == 0:
        callDict = radioDict.makeCallDictionary(offset, graphicsData)
    else:
        print(f'Graphics parse error offset {offset}! \n')
    
    output.write(f'Call Header: {humanFreq:.2f}, offset = {offset}, length = {length}, UNK0 = {unk0.hex()}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, Content = {line.hex()}\n')
    layerNum += 1

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
        elif radioData[offset + count].to_bytes() == b'\xff' and radioData[offset + count + 1].to_bytes() in commandNamesEng:
            break
        else: 
            count += 1
    content = radioData[offset: offset + count]
    
    if len(content) % 36 != 0: # Alert user if the graphics content not evenly divisible by 36 bytes
        output.write(f'ERROR! Unknown block at offset {offset}! ')

    """ Taking this out temporarily, we're exporting another way
    if exportGraphics: 
        if len(content) % 36 == 0:
            radioDict.outputManyGraphics(str(offset), content)
            output.write('Graphics output! -- ')
        else:
            output.write('ERROR! Graphics data was not even multiple of 36 bytes! -- ') # Redunant?

        output.write(f'Length = {count}, Graphics = {str(count / 36)} ')
        """
    output.write(f'Unknown block: {content.hex()}')
    output.write('\n')
    return count

def handleCommand(offset: int) -> int: # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    global output
    global layerNum
    jpn = True
    global root
    global elementStack

    # output.write(f'Offset is {offset}\n') # print for checking offset each loop
    commandByte = radioData[offset + 1].to_bytes() # Could add .hex() to just give hex digits
    
    indentLines() # Indent before printing the command to our depth level.

    # We now deal with the byte
    match commandByte:

        case b'\x00': # AKA A null, May want to correct this to ending a \x02 segment
            
            output.write(f'NULL (Command! offset = {offset})\n')
            if layerNum > 0:
                layerNum -= 1
            """if radioData[offset + 1] == b'\x31':
                length = handleCommand(offset + 1)
                return length + 7"""
            return 1
        
        case b'\x01':
            length = getLength(offset) 
            line = radioData[ offset : offset + length]
            output.write('Dialogue -- ')
            # Don't do logic for extra nulls, caught in main loop.
            face = line[4:6]
            anim = line[6:8]
            unk3 = line[8:10]
            dialogue = line[10 : length]
            2144
            lineBreakRepace = False
            if b'\x80\x23\x80\x4e' in dialogue:  # this replaces the in-game hex for new line with a \\r\\n
                lineBreakRepace = True
                dialogue = dialogue.replace(b'\x80\x23\x80\x4e', b'\x5c\x72\x5c\x6e')

            # Translate
            if jpn:
                if b'\x96\x00' in dialogue: # We need this because we should never see 0x9600
                    print(f'{offset} has a 0x9600 in dialogue! Check binary')
                # print(f'Offset is {offset}\n')
                translatedDialogue = translateJapaneseHex(dialogue) # We'll translate when its working
                dialogue = str(translatedDialogue)
            else:
                dialogue = dialogue.decode('ascii')

            output.write(f'Offset = {offset}, Length = {length}, FACE = {face.hex()}, ANIM = {anim.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, \tText: {(dialogue)}\n')
            
            subtitle_element = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                'face': face.hex(),
                "anim": anim.hex(),
                "unk3": unk3.hex(),
                "Text": dialogue
            })

            return length
        
        case b'\x02':
            output.write('VOX START! -- ')
            header = getLengthManually(offset)
            length = getLength(offset)
            line = radioData[offset : offset + header]
            voxLength1 = struct.unpack('>H',line[2:4])[0]
            voxLength2 = struct.unpack('>H',line[9:11])[0]
            
            # Check for even length numbers
            if debugOutput:
                if voxLength1 - voxLength2 != 7:
                    print(f'ERROR!! OFFSET {offset} HAS A \\x02 that does not evenly fit!')

            voxElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(voxLength1),
                "LengthB": str(voxLength2),
                "Content": f'{line.hex()}'
            })
            # checkElement(header)
            elementStack.append((voxElement, length))
            output.write(f'Offset: {str(offset)}, LengthA = {voxLength1}, LengthB = {voxLength2}, Content: {str(line.hex())}\n')
            
            return header
        
        case b'\x03':
            output.write('ANIMATE -- ')
            length = getLength(offset)
            line = radioData[offset : offset + length]
            containerLength = line[2:4]
            face = line[4:6]
            anim = line[6:8]
            buff = line[8:10]

            Anim_Element = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                'face': line[4:6].hex(),
                'anim': line[6:8].hex(),
                'buff': line[8:10].hex(),
            })

            output.write(f'Offset: {str(offset)}, length = {length} FACE = {face.hex()}, ANIM = {anim.hex()}, FullContent: {str(line.hex())}\n')
            return length
        
        case b'\x04':
            output.write('ADD FREQ -- ')
            length = getLength(offset)
            line = radioData[offset : offset + length]
            containerLength = getLength(offset)
            freq = getFreq(offset + 4)
            entryName = line[6 : length]
            if jpn:
                entryNameStr = translateJapaneseHex(entryName)
            else:
                entryNameStr = entryName.decode('ascii')

            # Just a safety since the length of this was hard-coded
            if debugOutput:
                if struct.unpack('>H', line[2:4])[0] != length - 2:
                    print(f'ERROR! Offset {offset} has an ADD_FREQ op that does not match its length!')

            SaveFreqElement = ET.SubElement(elementStack[-1][0], "Freq-add", {
                "offset": str(offset),
                "length": str(length),
                "freq": str(freq),
                "name": entryNameStr
            })

            output.write(f'Offset: {str(offset)}, length = {containerLength}, freqToAdd = {freq}, entryName = {entryName}, FullContent: {str(line.hex())}\n')
            return length
        
        case b'\x05':
            output.write(commandToEnglish(commandByte))
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
            output.write(commandToEnglish(commandByte))
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
            output.write(commandToEnglish(commandByte))
            length = getLength(offset)
            header = getLengthManually(offset) # Maybe not ?
            line = radioData[offset : offset + header]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            layerNum += 2

            conditionalElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "header": str(header),
                "content": line.hex(),
            })
            checkElement(length)
            elementStack.append((conditionalElement, length))
            return header
        
        case b'\x11' | b'\x12': # Elseif, Else respectively
            output.write(commandToEnglish(commandByte))
            header = getLengthManually(offset) # Maybe not ?
            length = getLength(offset + 1)
            line = radioData[offset : offset + header]
            output.write(f' -- Offset = {offset}, header = {header}, length = {length} Content = {line.hex()}\n')
            layerNum += 1

            elseElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "content": line.hex(),
            })
            checkElement(length)
            elementStack.append((elseElement, length))
            return header
        
        case b'\x30' | b'\x31':
            # 30 is handled different, as it has a container header
            if commandByte == b'\x30':
                length = getLengthManually(offset)
            else:
                length = 7 # Hard code this for now, works in most cases.
            line = radioData[offset : offset + length]
            output.write(commandToEnglish(commandByte))
            scriptLength = struct.unpack('>H',line[length - 2: length])[0]
            
            output.write(f' -- offset = {offset}, Script is {scriptLength} bytes, Content = {line.hex()}\n')

            randomElement = ET.SubElement(elementStack[-1][0], commandToEnglish(commandByte), {
                "offset": str(offset),
                "length": str(length),
                "content": line.hex()
            })
            return length 
        
        case b'\x40':
            output.write(commandToEnglish(commandByte))
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
        
        case b'\xFF': # This basically menas offset should be 1 less... we'll continue processing but output will error at this offset.
            output.write(f'ERROR! Command was 0xFF at offset {offset}!!! \n')
            if debugOutput:
                print(f'ERROR! Command was 0xFF at offset {offset}!!! \n')
            length = 1
            return length

        case _:
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
        if offset + count == fileSize:
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
    if len(elementStack) > 0:
        current_element, current_length = elementStack.pop()
        newElementLength = current_length - length
        if newElementLength > 0:
            elementStack.append((current_element, newElementLength))

## Translation Commands:
def translateJapaneseHex(bytestring: bytes) -> str: # Needs fixins, maybe move to separate file?
    global callDict
    return radioDict.translateJapaneseHex(bytestring, callDict)

def extractRadioCallHeaders(outputFilename: str) -> None:
    offset = 0
    global jpn
    global indentToggle
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
    output.close()

def analyzeRadioFile(outputFilename: str) -> None: # Cant decide on a good name, but this outputs a readable text file with the information broken down.
    offset = 0
    global layerNum
    # Settings
    global jpn
    global debugOutput
    global indentToggle

    global radioData
    global fileSize
    global output
    nullCount = 0
    
    setOutputFile(outputFilename)

    """
    # Probably unused/superfluous
    if radioData == None:
        return "Command failed! Radiodata file not set!"
    """

    while offset < fileSize - 1: # We might need to change this to Case When... as well.
        # Offset Tracking
        if debugOutput:
            print(f'Main loop: offset is {offset}')

        if nullCount == 4:
            output.write(f'ALERT!!! We just had 4x Nulls in a row at offset {offset}\n')
            nullCount = 0

        # MAIN LOGIC
        if radioData[offset].to_bytes() == b'\x00': # Add logic to tally the nulls for reading ease
            indentLines()
            if radioData[offset + 1].to_bytes() == b'\x31': # For some reason switch statements don't have an FF
                length = handleCommand(offset)
            else:
                output.write(f"Null! (Main loop) offset = {offset}\n")
                nullCount += 1
                if layerNum > 0:
                    layerNum -= 1
                length = 1
                nullElement = ET.SubElement(elementStack[-1][0], "Null", {"Offset": f'{offset}', "length": "1"})
                checkElement(1)
        elif radioData[offset].to_bytes() == b'\xFF': # Commands start with FF
            nullCount = 0
            if radioData[offset + 1].to_bytes() == b'\x01':
                length = handleCommand(offset)
            else:
                length = handleCommand(offset)
        elif checkFreq(offset): # If we're at the start of a call
            nullCount = 0
            handleCallHeader(offset)
            length = 11 # In this context, we only want the header
            layerNum = 1
        else: # Something went wrong, we need to kinda reset
            length = handleUnknown(offset) # This will go until we find a call frequency
            offset += length
            continue
            
        offset += length
        checkElement(length)

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
    parser = argparse.ArgumentParser(description=f'Parse a binary file for Codec call GCL. Ex. script.py <filename> <output.txt>')

    # REQUIRED
    parser.add_argument('filename', type=str, help="The call file to parse. Can be RADIO.DAT or a portion of it.")
    parser.add_argument('output', nargs="?", type=str, help="Output Filename (.txt)")
    # Optionals
    parser.add_argument('-v', '--verbose', action='store_true', help="Write any errors to stdout for help parsing the file")
    # parser.add_argument('-j', '--japanese', action='store_true', help="Toggles translation for Japanese text strings [BUG! CURRENTLY ALWAYS ENABLED!]") # Remove later when issue with english resolved
    parser.add_argument('-i', '--indent', action='store_true', help="Indents container blocks, WORK IN PROGRESS!")
    parser.add_argument('-s', '--split', action='store_true', help="Split calls into individual bin files")
    parser.add_argument('-H', '--headers', action='store_true', help="Extract call headers ONLY!")
    parser.add_argument('-g', '--graphics', action='store_true', help="export graphics")
    parser.add_argument('-x', '--xmloutput', action='store_true', help="Exports the call data into XML format")
    parser.add_argument('-z', '--iseeeva', action='store_true', help="Exports the dialogue in a json like Iseeeva's script")
    

    args = parser.parse_args()

    # Set input filename
    filename = args.filename
    baseFilename = filename.split("/")[-1]

    # Set output Filename
    if args.output:
        outputFilename = f'{args.output}'
    else:
        outputFilename = f'{baseFilename}-output'

    if args.verbose:
        debugOutput = True
    
    """ # BUG! Renable later when fixed
    if args.japanese:
        jpn = True
        """
    
    if args.indent:
        indentToggle = True
    
    if args.split:
        splitCalls = True
    
    if splitCalls:
        os.makedirs('extractedCallBins', exist_ok=True)
    
    if args.graphics:
        exportGraphics = True
    
    setRadioData(filename)
    radioDict.openRadioFile(filename)
    
    if args.headers:
        extractRadioCallHeaders(outputFilename)
    else:
        analyzeRadioFile(outputFilename)
    
    if args.graphics:
        exportGraphics = True

    fancy = True # For now this is the only way to properly output the file. 
    # Optional print the string: 
    if args.xmloutput:
        if fancy:
            from xml.dom.minidom import parseString
            xmlstr = parseString(ET.tostring(root)).toprettyxml(indent="  ")
            xmlFile = open(f'{args.output}.xml', 'w')
            xmlFile.write(xmlstr)
            xmlFile.close()
        else:
            # THE OLD METHOD! 
            xmlOut = ET.ElementTree(root)
            xmlOut.write(f"{outputFilename}.xml")
    
    if args.iseeeva:
        import json
        dialogueData = {}
        for subs in root.findall(f'.//SUBTITLE'):
            offset = subs.get('offset')
            text = subs.get('Text')
            dialogueData[int(offset)] = text
        
        with open(f"{outputFilename}-Iseeva.json", 'w') as f:
            json.dump(dialogueData, f, ensure_ascii=False, indent=4)
    
    if args.graphics:
        with open("graphicsExport/GraphicsFound.txt", 'w') as f:
            f.write(f'=================================\n')
            f.write(f"{filename} has these graphics that were unmatched:\n")
            # f.write(str(radioDict.foundGraphics))
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