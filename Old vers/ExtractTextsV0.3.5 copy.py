#!/bin/python

# Assumes RADIO.DAT for filename
"""
We can't get all the way through, so let's try parsing some calls.

Switching commands as I go to use the radioData as that would be in memory...
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
radioData = radioFile.read()
fileSize = radioData.__len__()

Header = radioData[ offset : offset + 8]
print(type(Header))
print(Header)

freq = struct.unpack('>h', Header[0:2])[0]
print(freq)
print(hex(freq))

command = b'\x80'
hex = command.decode('utf-8','')
print(f'Command: {command}, hex = {hex}')