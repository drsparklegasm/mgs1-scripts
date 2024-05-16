#!/bin/python

# Assumes RADIO.DAT for filename

"""
We can't get all the way through, so let's try parsing some calls.

v0.3.6: Adding a "Chunk pull" and "chunk analyzer"
v0.3.9: Removed Chunk pull
v0.4: Rebuild with FF as start of each command. 
"""
#    Project notes
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

def commandToEnglish(hex):
    global output
    try: 
        commandNamesEng[hex]
        return commandNamesEng[hex]
    except:
        return f'BYTE {hex.hex()} WAS NOT DEFINED!!!!'
    
def indentLines():
    if indentToggle == True:
        for x in range(layerNum):
            output.write('\t')

def checkFreq(offset): # Checks if the next two bytes are a codec number or not. Returns True or False.
    global radioData
    freq = struct.unpack('>h', radioData[offset : offset + 2])[0] # INT from two bytes
    if 14000 < freq < 14200:
        return True
    else: 
        return False
    
def getFreq(offset): # If freq is at offset, return frequency as 140.15
    global radioData

    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0]
    return freq / 100

def getLength(offset): # Returns COMMAND length, offset must be at the 0xff bytes
    global radioData
    
    lengthBytes = radioData[offset + 2: offset + 4]
    lengthT = struct.unpack('>H', lengthBytes)[0]
    return lengthT + 2

def getLengthManually(offset):
    length = 0
    while radioData[offset + length + 1].to_bytes() != b'\xff':
        length += 1
    length += 1
    return length 

def getCallLength(offset): # Returns CALL length, offset must be at the freq bytes
    global radioData

    lengthT = struct.unpack('>h', radioData[offset + 2 : offset + 4])[0]
    return lengthT

def handleCallHeader(offset): # Assume call is just an 8 byte header for now, then \x80, then script length (2x bytes)
    global radioData
    global output
    # output.write(f'Offset is {offset}\n') # print!!!
    header = radioData[ offset : offset + 11 ]

    # Separate the header
    humanFreq = getFreq(offset)
    face1 = header[2:4] # face 1
    face2 = header[4:6] # face 2
    unk0 = header[6:8] # Usually nulls
    callLength = header[9:11]
    numBytes = numBytes = struct.unpack('>h', callLength)[0]

    # Quick error checking
    if debugOutput:
        if header[8].to_bytes() != b'\x80':
            output.write(f'ERROR AT byte {offset}!! \\x80 was not found \n') # This means what we analyzed was not a call header!
            return False

    output.write(f'Call Header: {humanFreq}, {face1.hex()}, {face2.hex()}, {unk0.hex()}, Call is {numBytes} bytes long, offset: {offset}\n')
    return True

def handleUnknown(offset): # Iterates checking frequency until we get one that is valid.... hopefully this gets us past a chunk of unknown data.
    count = 0
    output.write(f'ERROR! Unknown blcok at offset {offset}! ')
    while True:
        if checkFreq(offset + count):
            break
        else: 
            count += 1
    content = radioData[offset: offset + count]
    output.write(f'Length = {count}, Unknown block: {content.hex()}\n')
    return count

def handleCommand(offset): # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    global radioData
    global output
    global layerNum
    # output.write(f'Offset is {offset}\n') # print for checking offset each loop
    commandByte = radioData[offset + 1].to_bytes() # Could add .hex() to just give hex digits
    indentLines() # Indent before printing the command to our depth level.

    # We now deal with the byte
    match commandByte:

        case b'\x00': # AKA A null, May want to correct this to ending a \x02 segment
            output.write('NULL (Command!)\n')
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
                dialogue = translateJapaneseHex(dialogue) # We'll translate when its working
            
            output.write(f'Offset = {offset}, Length = {length}, FACE = {face.hex()}, ANIM = {anim.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, \tText: {str(dialogue)}\n')

            return length
        
        case b'\x02':
            output.write('VOX START! -- ')
            header = 11
            length = getLength(offset)
            line = radioData[offset : offset + header]
            voxLength1 = struct.unpack('>h',line[2:4])[0]
            voxLength2 = struct.unpack('>h',line[9:11])[0]
            
            # Check for even length numbers
            if debugOutput:
                if voxLength1 - voxLength2 != 7:
                    print(f'ERROR!! OFFSET {offset} HAS A \\x02 that does not evenly fit!')

            output.write(f'Offset: {str(offset)}, LengthA = {voxLength1}, LengthB = {voxLength2}, Content: {str(line.hex())}\n')
            container(offset + header, length - header - 2) # ACCOUNT FOR HEADER AND LENGTH BYTES! 
            return header
        
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

            output.write(f'Offset: {str(offset)}, FACE = {face.hex()}, ANIM = {anim.hex()}, FullContent: {str(line.hex())}\n')
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

        case b'\x10' | b'\x11' | b'\x12': # If, ElseIF, Else respectively
            output.write(commandToEnglish(commandByte))
            length = getLength(offset)
            header = getLengthManually(offset) # Maybe not ?
            line = radioData[offset : offset + header]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')

            # Containerizing!
            # container(offset + header, length - header - 2)

            return length
        
        case b'\x40':
            output.write(commandToEnglish(commandByte))
            length = getLength(offset)
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            return length
        
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
        
        case b'\xFF':
            output.write(f'ERROR! Command was 0xFF at offset {offset}!!! \n')
            if debugOutput:
                print(f'ERROR! Command was 0xFF at offset {offset}!!! \n')
            length = 1
            return length

        case _:
            output.write(f'Command is not yet cased! Command = {commandByte} -- ')
            
            length = getLengthManually(offset)
            line = radioData[offset : offset + length]
            output.write(f'Offset: {offset}, Content = {line.hex()}\n')
            return length

def container(offset, length):
    counter = 0
    global layerNum
    internalOffset = offset
    layerNum += 1
    while counter < length:
        commandLength = handleCommand(internalOffset)
        internalOffset += commandLength
        counter += commandLength
    
    layerNum -= 1
    return length

## Translation Commands:

def translateJapaneseHex(bytestring): # Needs fixins
    i = 0
    messageString = ''

    while i < len(bytestring) - 1:
        try:
            messageString += radioDict.getRadioChar(bytestring[ i : i + 2 ].hex())
        except:
            output.write(f'Unable to translate Japanese byte code {bytestring[i : i+2].hex()}!!!\n')
            messageString += '[ERROR]'
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
        output.write("Null! (Main loop)\n")
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
        layerNum += 1
    elif radioData[offset] == b'\x31': # An not so elegant solution to finding case \x31
        nullCount = 0
        length = handleCommand(offset - 1)
    else: # Something went wrong, we need to kinda reset
        layerNum = 0
        length = handleUnknown(offset) # This will go until we find a call frequency
    offset += length

output.close()

if offset == fileSize:
    print(f'File was parsed successfully! Written to {outputFilename}')

""" This doesn't work because i did not code with contextual variables in mind >:O
if __name__ == '__main__':
    main()
"""