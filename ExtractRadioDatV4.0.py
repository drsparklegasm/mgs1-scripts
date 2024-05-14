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
# TODO: Container looping ?

import os, struct, re
import radioDict

## Formatting Settings!

jpn = False
indentToggle = False
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
    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0] # INT from two bytes

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
    return lengthT

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
    Freq = header[0:2]
    unk0 = header[2:4] # face 1
    unk1 = header[4:6] # face 2
    unk2 = header[6:8] # Usually nulls
    callLength = header[9:11]
    numBytes = 0

    # Quick error checking
    if header[8].to_bytes() == b'\x80':
        numBytes = struct.unpack('>h', callLength)[0]
    else:
        output.write(f'ERROR AT byte {offset}!! \\x80 was not found \n') # This means what we analyzed was not a call header!

    humanFreq = getFreq(offset)
    output.write(f'Call Header: {humanFreq}, {unk0}, {unk1}, {unk2}, Call is {numBytes} bytes long, offset: {offset}\n')
    return

def handleCommand(offset): # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    global radioData
    global output
    global layerNum
    # output.write(f'Offset is {offset}\n') # print for checking offset each loop
    commandByte = radioData[offset + 1].to_bytes() # Could add .hex() to just give hex digits
    indentLines()

    # We now deal with the byte
    match commandByte:

        case b'\x00': # AKA A null, May want to correct this to ending a \x02 segment
            output.write('NULL! found in HANDLE command! Was a container missed?\n')
            if radioData[offset + 1] == b'\x31':
                length = handleCommand(offset + 1)
                return length + 1
            return 1
        
        case b'\x01':
            length = getLength(offset) + 2
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
                # dialogue = translateJapaneseHex(dialogue) # We'll translate when its working
                output.write(f'Offset = {offset}, Length = {length}, FACE = {face.hex()}, ANIM = {anim.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, Text: {str(dialogue.hex())}\n')
            else:
                output.write(f'Offset = {offset}, Length = {length}, FACE = {face.hex()}, ANIM = {anim.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, Text: {str(dialogue)}\n')

            return length
        
        case b'\x02':
            output.write('VOX START! -- ')
            length = getLength(offset) + 2
            line = radioData[offset : offset + 11]
            voxLength1 = struct.unpack('>h',line[2:4])[0]
            voxLength2 = struct.unpack('>h',line[9:11])[0]
            
            # Check for even length numbers
            if debugOutput:
                if voxLength1 - voxLength2 != 7:
                    print(f'ERROR!! OFFSET {offset} HAS A \\x02 that does not evenly fit!')

            output.write(f'Offset: {str(offset)}, LengthA = {voxLength1}, LengthB = {voxLength2}, Content: {str(line.hex())}\n')
            container(offset + 11, length)
            return length
        
        case b'\x03':
            output.write('ANIMATE -- ')
            length = getLength(offset) + 2
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
            length = getLength(offset) + 2
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
        

        case b'\x10' :
            output.write(commandToEnglish(commandByte))
            length = getLengthManually(offset)
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            layerNum += 1
            return length
        
        case b'\x11': # Else
            output.write(commandToEnglish(commandByte))
            length = getLengthManually(offset)
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            layerNum += 1
            return length 
        
        case b'\x12': # Else IF
            output.write(commandToEnglish(commandByte))
            length = getLengthManually(offset)
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            layerNum += 1
            return length
        
        # This one is fugly. Time to look at containerizing these. 
        case b'\x31':
            if radioData[offset] == b'\xff':
                length = getLength() + 2
                line = radioData[offset : offset + length]
                output.write(commandToEnglish(commandByte))
                scriptLength = struct.unpack('>h',line[length - 2: length])[0]
            else:
                output.write(commandToEnglish(commandByte))
                length = 6
                line = radioData[offset : offset + 6]
                scriptLength = struct.unpack('>h',line[4:6])[0]
            output.write(f' -- Script is {scriptLength} bytes, Content = {line.hex()}\n')
            return length 
        
        case b'\xFF':
            return 1

        case _:
            output.write(f'Command is not yet cased! Command = {commandByte} -- ')
            
            if commandByte == b'\x10' or b'\x12':
                layerNum += 1
            
            length = getLengthManually(offset)
            line = radioData[offset : offset + length + 1]
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
    """ THIS DOES NOT YET WORK!
    i = 0
    messageString = ''

    while i < len(bytestring) - 1:
        messageString += radioDict.getRadioChar(bytestring[ i : i + 2 ].hex())
        i += 2
        """
    return 

while offset <= 1000: # fileSize - 1:
    # Offset Tracking
    if debugOutput:
        print(f'offset is {offset}')

    if radioData[offset].to_bytes() == b'\x00': # Add logic to tally the nulls for reading ease
        indentLines()
        output.write("Null!\n")
        offset += 1
        layerNum -= 1
    elif radioData[offset].to_bytes() == b'\xFF':
        length = handleCommand(offset)
        offset += length
    # elif radioData[offset].to_bytes() == b'\xFF' and radioData[offset + 1].to_bytes() == b'\x31'
    else:
        layerNum = 0
        handleCallHeader(offset)
        layerNum += 1
        offset += 11

output.close()

if offset == fileSize:
    print(f'File was parsed successfully! Written to {outputFilename}')

"""
if __name__ == '__main__':
    main()
"""