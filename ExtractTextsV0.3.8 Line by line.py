#!/bin/python

# Assumes RADIO.DAT for filename
"""
We can't get all the way through, so let's try parsing some calls.

v0.3.6: Adding a "Chunk pull" and "chunk analyzer"
"""


import os
import struct

filename = "/Users/solidmixer/projects/mgs1-undub/RADIO-usa.DAT"
#filename = "RADIO-jpn.DAT"

offset = 0
# offset = 293536 # Freq 140.85

radioFile = open(filename, 'rb')
output = open("output.txt", 'w')

offset = 0
radioData = radioFile.read() # The byte stream is better to use than the file on disk if you can. 
fileSize = radioData.__len__()



commandNamesEng = {b'\x01':'SUBTITLE', b'\x02':'VOX_CUES', b'\x03':'ANI_FACE', b'\x04':'ADD_FREQ',
                b'\x05':'MEM_SAVE', b'\x06':'AUD_CUES', b'\x07':'ASK_USER', b'\x08':'SAVEGAME',
                b'\x10':'IF_CHECK', b'\x11':'ELSE', b'\x12':'ELSE_IFS', b'\x30':'SWITCH',
                b'\x31':'SWITCHOP', b'\x80':'GCL_SCPT', b'\xFF':'ANIMATION', b'\x00':'NULL' 
}

def commandToEnglish(hex):
    try: 
        commandNamesEng[hex]
        return commandNamesEng[hex]
    except:
        return "BYTE WAS NOT DEFINED!!!!" 


# print(fileSize) # Result is 1776859! 

def checkFreq(offsetCheck): # Checks if the next two bytes are a codec number or not. Returns True or False.
    global radioData
    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0] # INT from two bytes

    if 14000 < freq < 14300:
        return True
    else: 
        return False

def getFreq(offsetCheck): # If freq is at offset, return frequency as 140.15
    global radioFile

    radioFile.seek(offsetCheck)
    bytes = radioFile.read(2)

    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0]
    return freq / 100

def getCallLength(offset): # Returns the length of the call, offset must be at the freq bytes
    global radioFile
    radioFile.seek(offset + 9) # Call length is after 8 bytes, then 0x80, then the length of the script in 2x bytes, then FF

    lengthBytes = radioFile.read(2)
    lengthT = struct.unpack('>h', lengthBytes)
    return lengthT[0]

def getLength(offsetCheck): # Returns the length of the command, offset must be at the freq bytes
    global radioData
    
    lengthBytes = radioData[offsetCheck + 1: offsetCheck + 3]
    lengthT = struct.unpack('>H', lengthBytes)[0]
    return lengthT

def getByteAtOffset(offsetCheck): # Returns a single byte, probably redundant
    global radioData
    return radioData[offsetCheck]

def handleCallHeader(offsetCheck): # Assume call is just an 8 byte header for now
    global radioFile
    global output
    radioFile.seek(offset)
    header = radioFile.read(12)

    # Separate the header
    Freq = header[0:2]
    unk0 = header[2:4]
    unk1 = header[4:6]
    unk2 = header[6:8]
    callLength = header[9:11]
    numBytes = 0

    if header[8] == b'\x80':
        numBytes = struct.unpack('>h', callLength)[0]
    else:
        output.write(f'ERROR AT HEX {offset}! \n')

    # Quick check we ended with an FF
    if header[11] == 255: # Having trouble with ff, using 255
        output.write('Call intro ended with FF successfully\n')
    else:
        output.write(f'Call header DID NOT end in FF! Check hex at {callLength}')

    output.write(f'Call Header: {Freq}, {unk0}, {unk1}, {unk2}, Call is {numBytes} bytes long, hex {callLength}:\n')
    return

def handleCommand(offsetCheck): # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    # global radioFile
    global radioData
    global output

    output.write(f'Handling the command... ')
    commandByte = radioData[offsetCheck] #.to_bytes()?
    output.write(f'Command is {commandByte}\n')

    if commandByte == b'\x00':
        return 1

    length = getLength(offsetCheck)
    output.write(f'Length of command is {length}\n')
    commandBytes = radioData[offset : offset + length + 2]
    print(commandByte, ": Offset: ", offsetCheck, " // Content: ", commandBytes, end="\n\n")
    return length + 2
    """
    match commandByte:
        case b'\x80':
            offsetCheck += 1
            length = getLength(offsetCheck)
            output.write(f'Length of command is {length}\n')
            commandBytes = radioData[offset:offset + length + 1]
            print(commandBytes, end="\n")
            return length + 1
        case _:
            return 8 #  We'll hope whatever we run into is just 8 bytes long. """

def getChunk(offsetCheck): # THIS IS NOT RETURNING A SUBSET OF THE BYTES! WTF!
    global radioFile
    global fileSize

    start = offsetCheck
    radioFile.seek(offsetCheck)
    for byte in radioFile.read():
        if byte == '\xFF':
            end = offsetCheck
            return radioData[start : end +1]
        else:
            offsetCheck += 1
    return b'\x00'


while offset < fileSize:
    offsetHex = hex(offset)
    perc = offset / fileSize * 100
    print(f'We are at {perc}% through the file')
    if offset >= fileSize - 1:
        print("Reached end of file!!!\n END PROGRAM")
        break
    if checkFreq(offset):
        freq = getFreq(offset)
        output.write(f"Call found! Frequency is {freq}\n")
        callLength = getCallLength(offset)
        output.write(f'Call is {callLength} bytes long')
        handleCallHeader(offset)
        offset += 12
        start = offset
    else:
        if radioData[offset] == 255: # Expressing FF as a byte string wasnt working :|
            output.write("We matched an FF\n")
            line = radioData[start : offset + 1]
            output.write(str(line))
            output.write('\n')
            print('Wrote line to file!\n')
            offset += 1
            start = offset
        else:
            offset += 1

# Close output file
output.close()