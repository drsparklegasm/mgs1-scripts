#!/bin/python

# Assumes RADIO.DAT for filename

"""
We can't get all the way through, so let's try parsing some calls.

v0.3.6: Adding a "Chunk pull" and "chunk analyzer"
v0.3.9: Removed Chunk pull
v0.4: Rebuild with FF as start of each command. 
"""


import os, struct, re
import radioDict

#filename = "/home/solidmixer/projects/mgs1-undub/RADIO-usa.DAT"
filename = "RADIO-usa.DAT"
#filename = "RADIO-jpn.DAT"

# We'll do a better check for this later. 
if 'jpn' in filename:
    jpn = True
else:
    jpn = False

radioFile = open(filename, 'rb')
output = open("output.txt", 'w')

offset = 0
radioData = radioFile.read() # The byte stream is better to use than the file on disk if you can. 
fileSize = len(radioData)

# print(fileSize) # Result is 1776859! 

# A lot of this is work in progress or guessing
commandNamesEng = {b'\x01':'SUBTITLE', b'\x02':'VOX_CUES', b'\x03':'ANI_FACE', b'\x04':'ADD_FREQ',
                b'\x05':'MEM_SAVE', b'\x06':'MUS_CUES', b'\x07':'ASK_USER', b'\x08':'SAVEGAME',
                b'\x10':'IF_CHECK', b'\x11':'ELSE', b'\x12':'ELSE_IFS', b'\x30':'SWITCH',
                b'\x31':'SWITCHOP', b'\x80':'GCL_SCPT', b'\xFF':'CMD_HEDR', b'\x00':'NULL' 
}

def commandToEnglish(hex):
    try: 
        commandNamesEng[hex]
        return commandNamesEng[hex]
    except:
        return "BYTE WAS NOT DEFINED!!!!" 
    
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
    return length

def getCallLength(offset): # Returns CALL length, offset must be at the freq bytes
    global radioData

    lengthT = struct.unpack('>h', radioData[offset + 2 : offset + 4])[0]
    return lengthT

def handleCallHeader(offset): # Assume call is just an 8 byte header for now, then \x80, then script length (2x bytes)
    global radioData
    global output
    # output.write(f'Offset is {offset}\n') # DEBUG!!!
    header = radioData[ offset : offset + 11 ]

    # Separate the header
    Freq = header[0:2]
    unk0 = header[2:4] # face 1
    unk1 = header[4:6] # face 2
    unk2 = header[6:8] # Usually nulls
    callLength = header[9:11]
    numBytes = 0

    if header[8].to_bytes() == b'\x80':
        numBytes = struct.unpack('>h', callLength)[0]
    else:
        output.write(f'ERROR AT byte {offset}!! \\x80 was not found \n')

    humanFreq = getFreq(offset)
    # lengthHex = numBytes.to_bytes().hex() # I don't think we can use to_bytes() with 2 byte ints
    output.write(f'Call Header: {humanFreq}, {unk0}, {unk1}, {unk2}, Call is {numBytes} bytes long, offset: {offset}\n')
    return

def handleCommand(offset): # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    # global radioFile
    global radioData
    global output
    # output.write(f'Offset is {offset}\n') # debug for checking offset each loop
    
    commandByte = radioData[offset + 1].to_bytes() # Could add .hex() to just give hex digits
    length = getLength(offset)
    line = radioData[ offset : offset + length + 2]
    
    match commandByte:

        case b'\x00': # AKA A null, May want to correct this to ending a \x02 segment
            output.write('NULL! found in HANDLE command! \n')
            return offset + 1
        
        case b'\x01':
            output.write('Dialogue -- ')
            # Don't do logic for extra nulls, caught in main loop.
            unk1 = line[4:6]
            unk2 = line[6:8]
            unk3 = line[8:10]
            dialogue = line[ 10 : length + 2]
            
            lineBreakRepace = False
            if b'\x80\x23\x80\x4e' in dialogue:  # this replaces the in-game hex for new line with a \\r\\n
                lineBreakRepace = True
                dialogue = dialogue.replace(b'\x80\x23\x80\x4e', b'\x5c\x72\x5c\x6e')

            if jpn:
                # dialogue = translateJapaneseHex(dialogue) # We'll translate when its working
                writeToFile = f'Length (int) = {length}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, Text: {str(dialogue.hex())}\n'
            else:
                writeToFile = f'Length (int) = {length}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, Text: {str(dialogue)}\n'

            # Write to file
            output.write(writeToFile)
            return length + 2
        
        case b'\x02':
            output.write('VOX START! -- ')
            
            length = getLengthManually(offset)
            
            # Don't do logic for extra nulls, caught in main loop.
            unk1 = line[4:6]
            unk2 = line[6:8]
            unk3 = line[8:10]
            dialogue = line[ 10 : length + 2]
            
            writeToFile = f'Length (int) = {length}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, UNK3 = {unk3.hex()}, Text: {str(dialogue)}\n'


            # Write to file
            output.write(writeToFile)
            return length + 2
            """
        case b'\x10':
            output.write(f'Command is not yet cased! IF statement = {commandByte.to_bytes().hex()} -- ')
            length = 1
            end = radioData[ooffsetffset + length]
            while end != b'\xff':
                end = radioData[offset + length]
                length += 1
            while radioData[offset].to_bytes() != b'\xFF':
                offset += 1
            line = radioData[offset : offset + length + 2]
            writeToFile = "Offset: " + str(offset) + " // Content: " + str(line.hex()) + "\n"
            output.write(writeToFile)
            return length + 2 
        """
        case _:
            output.write(f'Command is not yet cased! Command = {commandByte.hex()} -- ')

            length = 0
            while radioData[offset + length + 1].to_bytes() != b'\xff':
                length += 1
            
            line = radioData[offset : offset + length + 1]
            writeToFile = "Offset: " + str(offset) + " // Content: " + str(line.hex()) + "\n"
            output.write(writeToFile)
            return length + 1


## Translation Commands:

def translateJapaneseHex(bytestring):
    i = 0
    messageString = ''

    while i < len(bytestring) - 1:
        messageString += radioDict.getRadioChar(bytestring[ i : i + 2 ].hex())
        i += 2
    return messageString

offset = 0
while offset <= fileSize - 1:
    print(f'offset is {offset}')
    if radioData[offset].to_bytes() == b'\x00': # Add logic to tally the nulls for reading ease
        print(f'Null at offset {offset}')
        output.write("Null!\n")
        offset += 1
    elif radioData[offset].to_bytes() == b'\xFF':
        print(f'FF at offset {offset}')
        length = handleCommand(offset)
        offset += length
    else:
        print(f'Handling header at offset {offset}')
        handleCallHeader(offset)
        offset += 11

output.close()

# TODO: Handle other cases, fix natashas script breaking shit 