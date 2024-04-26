##!/bin/python3

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
output = open("output.txt", '+a')

offset = 0
fileSize = radioData.__len__()

# print(fileSize) # Result is 1776859! 

def checkFreq(offsetCheck):
    global radioFile
    radioFile.seek(offsetCheck)
    bytes = radioFile.read(2)
    freq = struct.unpack('>h', bytes)
    if 14000 < freq[0] < 14300:
        return True
    else: 
        return False

def getFreq(offsetCheck):
    global radioFile
    radioFile.seek(offsetCheck)
    bytes = radioFile.read(2)
    freq = struct.unpack('>h', bytes)
    return freq[0] / 100

def getCallLength(offset):
    global radioFile
    radioFile.seek(offset + 9) # Call length is after 8 bytes, then 0x80, then the length of the script?

    lengthBytes = radioFile.read(2)
    lengthT = struct.unpack('>h', lengthBytes)
    return lengthT[0]


# Right now this iterates how many calls match a pattern before this breaks

"""
def checkCalls():
    global offset
    global fileSize
    
    while offset < fileSize:
        
        
        i = getFreq(offset)
        length = getCallLength(offset)

        if 140 < i < 143:
            print(f'Call from {i} found! Offset is {hex(offset)}')
            offset += length + 9
        else:
            print(f"Something went wrong at offset {hex(offset)}!\nWe did not find a call!")
            byteTup = struct.unpack('s', radioFile.read(1))
            command = byteTup[0]
            print(hex(command))
        
        
        print(hex(offset)) 
    return
"""

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
    output.write(f'Call Header: {Freq}, {unk0}, {unk1}, {unk2} ')
                                 
    return

def handleCommand(offsetCheck):
    global radioFile
    global output

    output.write(f'Handling the command...\n')
    radioFile.seek(offsetCheck)
    commandByte = radioFile.read(1)
    command = commandByte.hex()
    output.write(f'command is {command}\n')


    match command: 
        case b'\x31':
            return "Switch Op?\n"
        case _:
            return "UNKNOWN!\n"

while offset < fileSize:
    if offset == fileSize:
            print("Offset and fileSize match!!!\n END PROGRAM")
            break
    if checkFreq(offset):
        freq = getFreq(offset)
        print(f"Call found! Frequency is {freq}\n")
        output.write(f'Call {freq}')
        handleCall(offset)
        offset += 8
    else:
        byte = getBytesAtOffset(offset)
        thisCommand = commandToEnglish(byte)
        print(thisCommand + " is the command to handle with value: " + str(byte))
        output.write(f'Command is {handleCommand}')
        commandToEnglish(byte)
        handleCommand(offset)
        offset += 1
        break


output.close()