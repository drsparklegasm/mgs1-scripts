#!/bin/python

# Assumes RADIO.DAT for filename

"""
We can't get all the way through, so let's try parsing some calls.

v0.3.6: Adding a "Chunk pull" and "chunk analyzer"
v0.3.9: Removed Chunk pull
v0.4: Rebuild with FF as start of each command. 
"""
# Project notes
# TODO: Handle other cases, fix natashas script breaking shit (Cases)
# TODO: Mei ling scripts fucked up
# TODO: CASE switching study
# TODO: Container looping ? # IF Statements break these right now

import os, struct, re
import radioDict
import argparse

## Formatting Settings!

jpn = False
indentToggle = True
debugOutput = True
filename = "RADIO-usa.DAT"
outputFilename = "Radio-decrypted.txt"

# Initalizing files
radioFile = open(filename, 'rb')
output = open(outputFilename, 'w')

# Script variables 
offset = 0
layerNum = 0
radioData = radioFile.read() # The byte stream is better to use than the file on disk if you can. 
fileSize = len(radioData)
contDepth = 0

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
                    b'\x40':'EVAL_CMD', 
                    b'\x80':'GCL_SCPT', 
                    b'\xFF':'CMD_HEDR',
                    b'\x00':'NULL' 
}

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

def checkFreq(offset: int) -> bool:  # Checks if the next two bytes are a codec number or not. Returns True or False.
    global radioData
    freq = struct.unpack('>h', radioData[offset : offset + 2])[0] # INT from two bytes
    if 14000 < freq < 14200:
        return True
    else: 
        return False
    
def getFreq(offset: int) -> float: # If freq is at offset, return frequency as 140.15
    global radioData

    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0]
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
        if radioData[offset + length].to_bytes() == b'\xff' and radioData[offset + length - 3].to_bytes() == b'\x80':
            return length

def getCallLength(offset: int) -> int: # Returns CALL length, offset must be at the freq bytes
    global radioData

    lengthT = struct.unpack('>h', radioData[offset + 2 : offset + 4])[0]
    return lengthT

def handleCallHeader(offset: int) -> int: # Assume call is just an 8 byte header for now, then \x80, then script length (2x bytes)
    global radioData
    global output
    global layerNum
    
    # OPTIONAL Add an offset tracker output?
    
    header = 11 # Call headers are static 11
    line = radioData[ offset : offset + header ]

    # Separate the header
    humanFreq = getFreq(offset)
    unk0 = line[2:4] # face 1
    unk1 = line[4:6] # face 2
    unk2 = line[6:8] # Usually nulls
    callLength = line[9:11]
    length = struct.unpack('>h', callLength)[0]

    # Quick error checking
    if debugOutput:
        if line[8].to_bytes() != b'\x80':
            output.write(f'ERROR! AT byte {offset}!! \\x80 was not found \n') # This means what we analyzed was not a call header!
            return False

    output.write(f'\nCall Header: {humanFreq}, offset = {offset}, length = {length}, UNK0 = {unk0.hex()}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, Content = {line.hex()}\n')
    layerNum += 1
    return header

def handleUnknown(offset: int) -> int: # Iterates checking frequency until we get one that is valid.... hopefully this gets us past a chunk of unknown data.
    count = 0
    output.write(f'ERROR! Unknown blcok at offset {offset}! ')
    while True:
        if checkFreq(offset + count):
            break
        elif radioData[offset + count].to_bytes() == b'\xff':
            break
        else: 
            count += 1
    content = radioData[offset: offset + count]
    output.write(f'Length = {count}, Unknown block: {content.hex()}\n')
    return count

def handleCommand(offset: int) -> int: # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    global radioData
    global output
    global contDepth
    global layerNum
    # output.write(f'Offset is {offset}\n') # print for checking offset each loop
    commandByte = radioData[offset + 1].to_bytes() # Could add .hex() to just give hex digits
    indentLines() # Indent before printing the command to our depth level.

    # We now deal with the byte
    match commandByte:

        case b'\x00': # AKA A null, May want to correct this to ending a \x02 segment
            output.write(f'NULL (Command! offset = {offset})\n')
            layerNum -= 1
            if radioData[offset + 1] == b'\x31':
                length = handleCommand(offset + 1)
                return length + 7
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
            
            lineBreakRepace = False
            if b'\x80\x23\x80\x4e' in dialogue:  # this replaces the in-game hex for new line with a \\r\\n
                lineBreakRepace = True
                dialogue = dialogue.replace(b'\x80\x23\x80\x4e', b'\x5c\x72\x5c\x6e')

            # Write to file
            if jpn:
                dialogue = str(dialogue.hex()) # We'll translate when its working
            
            output.write(f'Offset = {offset}, Length = {length}, FACE = {face.hex()}, ANIM = {anim.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, \tText: {str(dialogue)}\n')

            return length
        
        case b'\x02':
            output.write('VOX START! -- ')
            header = getLengthManually(offset)
            length = getLength(offset)
            line = radioData[offset : offset + header]
            voxLength1 = struct.unpack('>h',line[2:4])[0]
            voxLength2 = struct.unpack('>h',line[9:11])[0]
            
            # Check for even length numbers
            if debugOutput:
                if voxLength1 - voxLength2 != 7:
                    print(f'ERROR!! OFFSET {offset} HAS A \\x02 that does not evenly fit!')

            output.write(f'Offset: {str(offset)}, LengthA = {voxLength1}, LengthB = {voxLength2}, Content: {str(line.hex())}\n')
            container(offset + header, length - header) # ACCOUNT FOR HEADER AND LENGTH BYTES! This may be off... too bad!
            return length
        
        case b'\x03':
            output.write('ANIMATE -- ')
            length = getLength(offset)
            line = radioData[offset : offset + length]
            containerLength = line[2:4]
            face = line[4:6]
            anim = line[6:8]
            buff = line[8:10]

            """# Just a safety since the length of this was hard-coded
            if debugOutput:
                if struct.unpack('>h', line[2:4])[0] != 8:
                    print(f'ERROR! Offset {offset} has an ANIM that does not match its length!')"""

            output.write(f'Offset: {str(offset)}, length = {length} FACE = {face.hex()}, ANIM = {anim.hex()}, FullContent: {str(line.hex())}\n')
            return length
        
        case b'\x04':
            output.write('ADD FREQ -- ')
            length = getLength(offset)
            line = radioData[offset : offset + length]
            containerLength = getLength(offset)
            freq = getFreq(offset + 4)
            entryName = line[6 : length - 1]

            # Just a safety since the length of this was hard-coded
            if debugOutput:
                if struct.unpack('>h', line[2:4])[0] != length - 2:
                    print(f'ERROR! Offset {offset} has an ADD_FREQ op that does not match its length!')

            output.write(f'Offset: {str(offset)}, length = {containerLength}, freqToAdd = {freq}, entryName = {entryName}, FullContent: {str(line.hex())}\n')
            return length
        
        case b'\x06' | b'\x07': 
            output.write(commandToEnglish(commandByte))
            length = getLength(offset)
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')

            return length

        case b'\x10': # If, ElseIF, Else respectively
            output.write(commandToEnglish(commandByte))
            length = getLength(offset)
            header = getLengthManually(offset) # Maybe not ?
            line = radioData[offset : offset + header]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            """
            # Containerizing!
            contDepth += 1
            container(offset + header, length - header - 2)
            contDepth -= 1
            """
            layerNum += 1
            return header
        
        case b'\x11' | b'\x12': # If, ElseIF, Else respectively
            output.write(commandToEnglish(commandByte))
            header = getLengthManually(offset) # Maybe not ?
            length = getLength(offset + header - 2)
            line = radioData[offset : offset + header]
            output.write(f' -- Offset = {offset}, length = {header}, length = {length} Content = {line.hex()}\n')

            """
            # Containerizing!
            contDepth += 1
            container(offset + header - 2, length - header - 2)
            contDepth -= 1
            """
            layerNum += 1
            return header
        
        # This one is fugly. Time to look at containerizing these or something. 
        case b'\x31':
            if radioData[offset] == b'\xff':
                length = getLengthManually()
                line = radioData[offset : offset + length]
                output.write(commandToEnglish(commandByte))
                scriptLength = struct.unpack('>h',line[length - 2: length])[0]
            else:
                output.write(commandToEnglish(commandByte))
                length = 7
                line = radioData[offset : offset + length]
                scriptLength = struct.unpack('>h',line[length - 2 : length])[0]
            output.write(f' -- offset = {offset}, Script is {scriptLength} bytes, Content = {line.hex()}\n')
            return length 
        
        case b'\x40':
            output.write(commandToEnglish(commandByte))
            # The last bytes in the 0x40 expression are 14 31 00...
            length = 0
            while True:
                length += 1
                if radioData[offset + length].to_bytes() == b'\x00':
                    if radioData[offset + length - 2].to_bytes() == b'\x14' and radioData[offset + length - 1].to_bytes() == b'\x31':
                        break

            length += 1
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            return length
        
        case b'\xFF':
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

def container(offset, length):
    counter = 0
    global layerNum
    global contDepth
    internalOffset = offset
    layerNum += 1
    while counter < length:
        if radioData[internalOffset].to_bytes() == b'\x00':
            commandLength = handleCommand(internalOffset - 1) # This is to still write a null (as an end of line) as a command.
        else:
            commandLength = handleCommand(internalOffset)
        internalOffset += commandLength
        counter += commandLength
    
    
    return length

## Translation Commands:

def translateJapaneseHex(bytestring): # Needs fixins
    i = 0
    messageString = ''

    while i < len(bytestring) :
        try:
            messageString += radioDict.getRadioChar(bytestring[ i : i + 2 ].hex())
        except:
            output.write(f'Unable to translate Japanese byte code {bytestring[i : i+2].hex()}!!!\n')
            messageString += '[ERROR!]'
        i += 2
        
    return messageString

nullCount = 0
while offset <= fileSize - 1: # We might need to change this to Case When... as well.
    # Offset Tracking
    if debugOutput:
        print(f'offset is {offset}')

    if nullCount == 4:
        output.write(f'ALERT!!! We just had 4x Nulls in a row at offset {offset}\n')
        nullCount = 0

    # MAIN LOGIC
    if radioData[offset].to_bytes() == b'\x00': # Add logic to tally the nulls for reading ease
        indentLines()
        output.write(f"Null! (Main loop) offset = {offset}\n")
        nullCount += 1
        layerNum -= 1
        length = 1
    elif radioData[offset].to_bytes() == b'\xFF': # Commands start with FF
        nullCount = 0
        length = handleCommand(offset)
    # elif radioData[offset].to_bytes() == b'\xFF' and radioData[offset + 1].to_bytes() == b'\x31'
    elif checkFreq(offset):
        nullCount = 0
        handleCallHeader(offset)
        length = 11
        layerNum = 1
    elif radioData[offset].to_bytes() == b'\x31': # An not so elegant solution to finding case \x31
        nullCount = 0
        length = handleCommand(offset - 1)
    else: # Something went wrong, we need to kinda reset
        length = handleUnknown(offset) # This will go until we find a call frequency
    offset += length

output.close()

if offset == fileSize:
    print(f'File was parsed successfully! Written to {outputFilename}')

""" This doesn't work because i did not code with contextual variables in mind >:O
if __name__ == '__main__':
    main()
"""