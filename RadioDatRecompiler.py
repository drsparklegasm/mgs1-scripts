"""
Recompiler for MGS RADIO.DAT files. This requires exported Radio XML and .json files created by RadioDatTools.py

Steps to use for translation:

1. Export XML and Json from RadioDatTools from source disk RADIO.DAT
2. Adjust dialogue in the .json file.
3. Run script with both files as arguments. 

We will output to RADIO.DAT or optionally a filename of your choice. 

"""


def realignOffsets():
    print(f'Offset integrity reviewed and done')

def createBinary():
    print(f'Binary data created')

def outputFile():
    print(f'File has been saved!')

import os, struct
import radioDict 
import argparse
import xml.etree.ElementTree as ET

inputXML = 'input.xml'

radioSource = ET.parse(inputXML)

for call in radioSource.findall(".//Call"):
    callHeader = b''

