#!/bin/python
"""
This script is to extact a specific radio call to another file. 
I find it's easier to study the raw hex on a subset of it, rather than the whole file.
Have offsets ready or refer to the bin file. Modify the filename for your Radio.dat file.
"""

import os, struct, re

filename = "RADIO-jpn.DAT"
"""
def __init__(self, radioFilename: str) -> None:
    os.makedirs("Extracted-Calls", 755, exist_ok=True)
    if not os.path.exists(filename):
        print(f'File {radioFilename} does not exist! Check path and try again.\n')
    else:
        radioFile = open(radioFilename, 'rb')
        radioData = radioFilename.read()
        print(f'Exporter Ready!')

"""




def main():
    
    print("Please provide offsets for the call in decimal forrmat (not hex)!")

    # Get in/out from user
    startOffset = int(input("First offset? (Int): "))
    endOffset = int(input("End offset? (Int): "))
    outputFile = input("Name of extracted call? ")

    """
    General notes:

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
    return


def splitCall(offset: int, length: int) -> None:
    global radioData
    splitCall = radioData[offset:offset+length]
    filename = str(offset) + '.bin'
    f = open(filename, 'wb')
    f.write(splitCall)
    f.close()
    return 0


if __name__ == '__main__':
    main()