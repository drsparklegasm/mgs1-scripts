##!/bin/python3

# Assumes RADIO.DAT for filename
"""
At this point we're just ensuring that each call has a correct length variable at the 9th byte

"""

import os
import struct

filename = "RADIO-usa.DAT"
#filename = "RADIO-jpn.DAT"

offset = 0
# offset = 293536 # Freq 140.85

radioFile = open(filename, 'rb')

radioData = radioFile.read()
offset = 0
fileSize = radioData.__len__()

# print(fileSize) 1776859! 

def getFreq(offsetCheck):
    global radioData
    global radioFile
    radioFile.seek(offsetCheck)
    bytes = radioFile.read(2)
    freq = struct.unpack('>h', bytes)
    return freq[0] / 100

def getCallLength(offset):
    global radioFile
    radioFile.seek(offset + 9)
    lengthBytes = radioFile.read(2)
    lengthT = struct.unpack('>h', lengthBytes)
    return lengthT[0]


# Right now this iterates how many calls match a pattern before this breaks
while offset < fileSize:
    if offset == fileSize:
        print("Offset and fileSize match!!!")
        break
    
    i = getFreq(offset)
    length = getCallLength(offset)

    if 140 < i < 143:
        print(f'Call from {i} found! Offset is {hex(offset)}')
        offset += length + 9
    else:
        print(f"Something went wrong at offset {hex(offset)}!\nWe did not find a call!")
        byteTup = struct.unpack('s', radioFile.read(1))
        command = byteTup[0]
        print(command)
        offset += length + 9 + 36
    
    
    print(hex(offset)) 




"""
Going specifically by call won't work... let's try going by command one at a time. 
"""



"""
freq = struct.unpack('>h', radioFile.read(2))

print(type(freq))
if 14000 < freq[0] < 14300:    print(str(freq[0]) + f' is the first call')


def checkIsFreq(checkByte):
    global radioFile
    bytes = struct.unpack('>h', checkByte)
    freq = bytes[0] / 100
    print(freq)
    if 140 < freq < 143:
        return True
    else:
        return False

checkByte = radioFile.read(2)
offset += 2
if checkIsFreq(checkByte):
    callHeader = radioFile.read(10)
    offset += 10
    # Perform 3 additional operations
    unk0 = callHeader[0:2]
    unk1 = callHeader[2:4]
    unk2 = callHeader[4:6]
    print(callHeader)
    print(unk0)
    print(unk1)
    print(unk2)
    # Optional check that unk2 is always 0x00 0x00 ?
    buffer = callHeader[7:9]
    length = struct.unpack('>h', buffer)
    print(length[0]) # this is the length we need to pull next 
    

"""

