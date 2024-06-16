#!/bin/python
"""
This script is to extact a specific radio call to another file. 
I find it's easier to study the raw hex on a subset of it, rather than the whole file.
Have offsets ready or refer to the bin file. Modify the filename for your Radio.dat file.
"""

import os, struct, re, argparse

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




def main(filename, offset, length):
    
    print("Please provide offsets for the call in decimal forrmat (not hex)!")

    # Get in/out from user
    startOffset = offset
    endOffset = offset + length
    outputFile = str(offset) + '.bin'

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
    """parser = argparse.ArgumentParser(description=f'Parse a binary file for Codec call GCL. Ex. script.py <filename> <output.txt>')

    # REQUIRED
    parser.add_argument('offset', type=int, help="Offset of the start of the")
    parser.add_argument('output', type=str, help="Output Filename (.txt)")
    """
    main("", int(), int())
    # main("radioDatFiles/RADIO-usa-d1.DAT", int(26213), int(324))