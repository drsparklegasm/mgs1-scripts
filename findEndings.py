import os, struct, re
import radioDict # May remove later
import argparse

offset = 0

radioFile = open("radioDatFiles/RADIO-usa-d1.DAT", 'rb')
radioData = radioFile.read()

def getLength(offset: int):
    length = struct.unpack('>H', radioData[offset + 2:offset + 4])[0] + 2
    return length

while offset < len(radioData):
    if radioData[offset:offset+2] == bytes.fromhex("ff10") or radioData[offset:offset+2] == bytes.fromhex("ff11"):
        length = getLength(offset)
        print(f'{offset}, {length}, {offset + length}, \'{radioData[offset + length - 6: offset + length].hex()}\', \'{radioData[offset + length: offset + length + 4].hex()}\'')
    offset += 1