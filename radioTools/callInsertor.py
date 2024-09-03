#!/bin/python
"""
This script is to extact a specific radio call to another file. 
I find it's easier to study the raw hex on a subset of it, rather than the whole file.
Have offsets ready or refer to the bin file. Modify the filename for your Radio.dat file.
"""

import os, struct, re, argparse

filename = "14085-testing/RADIO-jpn-d1.DAT"
updatedCall = "283744-new-mod.bin"
offset = 283744

radioFile = open(filename, 'rb')
radioData = radioFile.read()

newCallFile = open(updatedCall, 'rb')
newCallData = newCallFile.read()

newFileData = radioData[0: offset]
newFileData += newCallData
newFileData += radioData[ len(newFileData) : len(radioData) ]

if len(newFileData) == len(radioData):
    print(f'Success! Files are the same length')
    newFile = open('14085-testing/RADIO.DAT-modified', 'wb')
    newFile.write(newFileData)
    newFile.close
else:  
    print(f'File lengths differ! New: {len(newFileData)}, old: {len(radioData)}')


def splitCall(offset: int, length: int) -> None:
    global radioData
    splitCall = radioData[offset:offset+length]
    filename = str(offset) + '.bin'
    f = open(filename, 'wb')
    f.write(splitCall)
    f.close()
    return 0

