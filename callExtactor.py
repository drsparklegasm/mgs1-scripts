#!/bin/python
"""
This script is to extact a specific radio call to another file. 
I find it's easier to study the raw hex on a subset of it, rather than the whole file.
Have offsets ready or refer to the bin file. Modify the filename for your Radio.dat file.
"""

import os, struct, re
import radioDict

filename = "RADIO-jpn.DAT"
print("Please provide offsets for the call in decimal forrmat (not hex)!")

# Get in/out from user
startOffset = int(input("First offset? (Int): "))
endOffset = int(input("End offset? (Int): "))
outputFile = input("Name of extracted call? ")

"""
startOffset = 293536
endOffset = 294379
offset = 293536 # Freq 140.85 Hex 0x047AA0

140.85/jpn: 0x45460 --> 0x4572F // 283744 --> 284463

Offset = 1773852 # Deepthroat 140.48 Hex 0x1B111C, ends 
"""

radioFile = open(filename, 'rb')
output = open(outputFile, 'wb')

# fileSize = len(radioFile)

radioFile.seek(startOffset)
output.write(radioFile.read(endOffset - startOffset))

output.close()