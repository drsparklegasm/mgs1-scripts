##!/bin/python3

# Assumes RADIO.DAT for filename

import os
import struct

filename = "RADIO.DAT"
offset = 0

radioFile = open(filename, 'rb')

"""
freq = struct.unpack('>h', radioFile.read(2))

print(type(freq))
if 14000 < freq[0] < 14300:    print(str(freq[0]) + f' is the first call')
"""

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
    length = struct.unpack('>h', radioFile.read(offset))
    print(length[0]) # this is the length we need to pull next 
    

    

