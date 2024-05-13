#!/bin/python
"""
This script is to extact a specific radio call to another file. 
Have offsets ready or refer to the bin file. 
"""

import os, struct, re
import radioDict

filename = "RADIO-usa.DAT"

# Get in/out from user
startOffset = input("First offset? (Int): ")
endOffset = input("End offset? (Int): ")
outputFile = input("Name of extracted call? ")

"""
startOffset = 293536
endOffset = 294379
offset = 293536 # Freq 140.85 Hex 0x047AA0

Offset = 1773852 # Deepthroat 140.48 Hex 0x1B111C, ends 
"""

radioFile = open(filename, 'rb')
output = open(outputFile, 'wb')

# fileSize = len(radioFile)

radioFile.seek(startOffset)
output.write(radioFile.read(endOffset - startOffset))

output.close()