#!/bin/python
"""
This script is to extact a specific radio call to another file. 
Set the offsets manually below

"""

import os, struct, re
import radioDict

filename = "RADIO-usa.DAT"


startOffset = 293536
endOffset = 294379
# offset = 293536 # Freq 140.85 Hex 0x047AA0
# Offset = 1773852 # Deepthroat 140.48 Hex 0x1B111C, ends 

radioFile = open(filename, 'rb')
output = open("140.85.bin", 'wb')

fileSize = len(radioData)

radioFile.seek(startOffset)
output.write(radioFile)
