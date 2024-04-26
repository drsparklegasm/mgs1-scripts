#!/bin/python

# Assumes RADIO.DAT for filename
"""
We can't get all the way through, so let's try parsing some calls.
"""

import os
import struct

filename = "RADIO-usa.DAT"
#filename = "RADIO-jpn.DAT"

offset = 0
# offset = 293536 # Freq 140.85

radioFile = open(filename, 'rb')
output = open("output.txt", 'w')

offset = 0
radioData = radioFile.read() # The byte stream is better to use than the file on disk if you can. 
fileSize = radioData.__len__()



commandNamesEng = {b'\x01':'SUBTITLE', b'\x02':'VOX_CUES', b'\x03':'ANI_FACE', b'\x04':'ADD_FREQ',
                b'\x05':'MEM_SAVE', b'\x06':'AUD_CUES', b'\x07':'ASK_USER', b'\x08':'SAVEGAME',
                b'\x10':'IF_CHECK', b'\x11':'ELSE', b'\x12':'ELSE_IFS', b'\x30':'SWITCH',
                b'\x31':'SWITCHOP', b'\x80':'GCL_SCPT', b'\xFF':'ANIMATION', b'\x00':'NULL' 
}

def commandToEnglish(hex):
    try: 
        commandNamesEng[hex]
        return commandNamesEng[hex]
    except:
        return "BYTE WAS NOT DEFINED!!!!" 


# print(fileSize) # Result is 1776859! 

def checkFreq(offsetCheck):
    # Checks if the next two bytes are a codec number or not.
    global radioData
    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0] # INT from two bytes

    if 14000 < freq < 14300:
        return True
    else: 
        return False

def getFreq(offsetCheck):
    global radioFile

    radioFile.seek(offsetCheck)
    bytes = radioFile.read(2)

    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0]
    return freq / 100

def getCallLength(offset):
    global radioFile
    radioFile.seek(offset + 9) # Call length is after 8 bytes, then 0x80, then the length of the script?

    lengthBytes = radioFile.read(2)
    lengthT = struct.unpack('>h', lengthBytes)
    return lengthT[0]


def getBytesAtOffset(offset):
    global radioFile
    radioFile.seek(offset)
    byte = radioFile.read(1)
    return byte

def handleCall(offsetCheck): # Assume call is just an 8 byte header for now
    global radioFile
    global output
    radioFile.seek(offset)
    header = radioFile.read(8)

    # Separate the header
    Freq = header[0:2]
    unk0 = header[2:4]
    unk1 = header[4:6]
    unk2 = header[6:8]
    output.write(f'Call Header: {Freq}, {unk0}, {unk1}, {unk2} \n')
    return

def handleCommand(offsetCheck):
    global radioFile
    global output

    output.write(f'Handling the command...\n')
    commandByte = radioData[offsetCheck].to_bytes()
    output.write(f'command is {commandByte}\n')
    
    match commandByte:
        case b'\x80':
            offsetCheck += 1
            length = struct.unpack('>h', radioData[ offsetCheck : offsetCheck + 2])[0]
            output.write(f'Length of command is {length}\n')
            
            return length + 1
        case _:
            return 8


while offset < fileSize:
    offsetHex = hex(offset)
    output.write(f'Loop start! Offset is currently {offset} or {offsetHex}\n')
    if offset == fileSize:
            print("Offset and fileSize match!!!\n END PROGRAM")
            break
    if checkFreq(offset):
        freq = getFreq(offset)
        print(f"Call found! Frequency is {freq}\n")
        handleCall(offset)
        offset += 8
    else:
        byte = getBytesAtOffset(offset)
        thisCommand = commandToEnglish(byte)
        print(thisCommand + " is the command to handle with value: " + str(byte))
        byteInt = byte[0]


        commandToEnglish(byte)
        length = handleCommand(offset)
        offset += length 


output.close()