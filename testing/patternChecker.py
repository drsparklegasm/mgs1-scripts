import os, struct
from datetime import datetime
import radioDict 
import argparse
import xml.etree.ElementTree as ET

radioFile = "radioDatFiles/RADIO-usa-d1.DAT"
radioData = open(radioFile, 'rb').read()

size = len(radioData)
patterns = {}

def getLength(offset: int) -> int: # Returns COMMAND length, offset must be at the 0xff bytes, length is bytes 1 and 2.
    global radioData
    
    lengthBytes = radioData[offset + 2: offset + 4]
    length = struct.unpack('>H', lengthBytes)[0]
    return length + 2

def getLengthManually(offset: int) -> int:
    length = 0
    while True:
        length += 1
        if radioData[offset + length].to_bytes() == b'\xff' and radioData[offset + length - 3].to_bytes() == b'\x80':
            return length
        
pattern = 'ff10'
command = bytes.fromhex(pattern)

offset = 0

while offset < size:
    if radioData[offset : offset + 2] == command:        
        header = getLengthManually(offset) 
        line = radioData[offset : offset + header]

        # print(f'Offset: {offset}, Header: {header}')
        lengthA = getLength(offset)
        lengthB = getLength(offset + header - 4)
        lABytes = radioData[offset + 2: offset + 4].hex()
        lBBytes = radioData[offset + header - 2: offset + header].hex()
        """
        print(lengthA)
        print(lengthB)
        print(lABytes)
        print(lBBytes)
        """

        if lengthA == lengthB + header - 3:
            print(f'FF10 at offset {offset} length matched!')
        else:
            elseOffset = offset + header + lengthB - 4
            if radioData[elseOffset: elseOffset + 2] in [bytes.fromhex("ff11"), bytes.fromhex("ff12")]:
                # print(f'0x{radioData[elseOffset: elseOffset + 2].hex()}')
                elseLength = getLengthManually(elseOffset)
                print(f"FF10 at offset {offset} has a subclause. Else statement matched!")
            # else:
                # print(f'MO MATCH! 0x{radioData[elseOffset: elseOffset + 2].hex()}')
                # print(f"FF10 at offset {offset} has a subclause. Else statement WAS NOT MATCHED! \n\tBytes: {radioData[elseOffset : elseOffset + 5].hex()}")
        
    offset += 1

for line in patterns:
    print(line)
    
#print(patterns)

        