#!/bin/python
import argparse, os
import RadioDatTools as RDT

# Globals
debugOutput = True
jpn = False
indentToggle = True

# File variables
fileSize = 0

def analyzeRadioFile() -> None:
    offset = 0
    nullCount = 0
    
    while offset < fileSize - 1: # We might need to change this to Case When... as well.
        # Offset Tracking
        if debugOutput:
            print(f'Main loop: offset is {offset}')

        if nullCount == 4:
            RDT.output.write(f'ALERT!!! We just had 4x Nulls in a row at offset {offset}\n')
            nullCount = 0

        # MAIN LOGIC
        if radioData[offset].to_bytes() == b'\x00': # Add logic to tally the nulls for reading ease
            RDT.indentLines()
            if radioData[offset + 1].to_bytes() == b'\x31': # For some reason switch statements don't have an FF
                length = RDT.handleCommand(offset)
            else:
                RDT.output.write(f"Null! (Main loop) offset = {offset}\n")
                nullCount += 1
                if layerNum > 0:
                    layerNum -= 1
                length = 1
        elif radioData[offset].to_bytes() == b'\xFF': # Commands start with FF
            nullCount = 0
            length = RDT.handleCommand(offset)
        elif RDT.checkFreq(offset): # If we're at the start of a call
            nullCount = 0
            RDT.handleCallHeader(offset)
            length = 11 # In this context, we only want the header
            layerNum = 1
        else: # Something went wrong, we need to kinda reset
            length = RDT.handleUnknown(offset) # This will go until we find a call frequency
        offset += length

    RDT.output.close()

def extractRadioCallHeaders(filename: str) -> None:
    offset = 0
    global jpn
    global indentToggle
    global debugOutput
    global fileSize
    
    # Handle inputting radio file:
    global radioFile
    global radioData
    """
    radioFile = open(filename, 'rb')
    radioData = radioFile.read()
    fileSize = len(radioData)
    """
    RDT.setOutputFile(filename)

    while offset < fileSize - 1: # We might need to change this to Case When... as well.
        # Offset Tracking
        if debugOutput:
            print(f'offset is {offset}')

        # MAIN LOGIC
        if radioData[offset].to_bytes() == b'\x00': # Add logic to tally the nulls for reading ease
            length = 1
        elif RDT.checkFreq(offset):
            length = RDT.handleCallHeader(offset) 
        else:
            length = 1
        offset += length 
        if offset == fileSize:
            print(f'File was parsed successfully! Written to {filename}')
            break
    
    RDT.output.close()

def main():
    # Parser logic
    parser = argparse.ArgumentParser(description=f'Parse a binary file for Codec call GCL. Ex. script.py <filename> <output.txt>')

    parser.add_argument('filename', required=False, type=str, help="The call file to parse. Can be RADIO.DAT or a portion of it.")
    parser.add_argument('-o', '--output', type=str, required=False, help="(Optional) Provides an output file (.txt)")
    
    parser.add_argument('-v', '--verbose', action='store_true', help="Write any errors to stdout for help parsing the file")
    parser.add_argument('-j', '--japanese', action='store_true', help="Toggles translation for Japanese text strings")
    parser.add_argument('-i', '--indent', action='store_true', help="Indents container blocks, WORK IN PROGRESS!")
    args = parser.parse_args()

    if not args.filename:
        args.filename = os.read(f'Please provide filename: ')
    if args.verbose:
        debugOutput = True
    
    if args.japanese:
        jpn = True
    
    if args.indent:
        indentToggle = True
    
    if args.output:
        output = open(args.output, 'w')
        outputFilename = args.output
    
    # Handle inputting radio file:
    global radioFile
    global radioData
    global fileSize

    radioFile = open(args.filename, 'rb')
    #radioFile = open(filename, 'rb')
    radioData = radioFile.read()
    fileSize = len(radioData)

    extractRadioCallHeaders('headers.txt')
    analyzeRadioFile()

    



# This doesn't work because i did not code with contextual variables in mind >:O
if __name__ == '__main__':
    # We should get args from user. Using argParse
    # main()

        # Parser logic
    parser = argparse.ArgumentParser(description=f'Parse a binary file for Codec call GCL. Ex. script.py <filename> <output.txt>')

    parser.add_argument('filename', type=str, help="The call file to parse. Can be RADIO.DAT or a portion of it.")
    parser.add_argument('-o', '--output', type=str, required=False, help="(Optional) Provides an output file (.txt)")
    
    parser.add_argument('-v', '--verbose', action='store_true', help="Write any errors to stdout for help parsing the file")
    parser.add_argument('-j', '--japanese', action='store_true', help="Toggles translation for Japanese text strings")
    parser.add_argument('-i', '--indent', action='store_true', help="Indents container blocks, WORK IN PROGRESS!")
    args = parser.parse_args()

    if not args.filename:
        args.filename = os.read(f'Please provide filename: ')
    if args.verbose:
        debugOutput = True
    
    if args.japanese:
        jpn = True
    
    if args.indent:
        indentToggle = True
    
    if args.output:
        output = open(args.output, 'w')
        outputFilename = args.output
    
    # Handle inputting radio file:
    global radioFile
    global radioData
    fileSize

    radioFile = open(args.filename, 'rb')
    #radioFile = open(filename, 'rb')
    radioData = radioFile.read()
    fileSize = len(radioData)

    extractRadioCallHeaders('headers.txt')
    analyzeRadioFile()