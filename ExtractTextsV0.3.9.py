#!/bin/python

# Assumes RADIO.DAT for filename

"""
We can't get all the way through, so let's try parsing some calls.

v0.3.6: Adding a "Chunk pull" and "chunk analyzer"
v0.3.9: Removed Chunk pull
"""


import os, struct, re
import radioDict

#filename = "/home/solidmixer/projects/mgs1-undub/RADIO-usa.DAT"
filename = "../../RADIO-usa.DAT"
#filename = "../../RADIO-jpn.DAT"


if filename.__contains__('jpn'):
    jpn = True
else:
    jpn = False

offset = 0
# offset = 293536 # Freq 140.85

radioFile = open(filename, 'rb')
output = open("output.txt", 'w')

offset = 0
radioData = radioFile.read() # The byte stream is better to use than the file on disk if you can. 
fileSize = radioData.__len__()

# print(fileSize) # Result is 1776859! 

commandNamesEng = {b'\x01':'SUBTITLE', b'\x02':'VOX_CUES', b'\x03':'ANI_FACE', b'\x04':'ADD_FREQ',
                b'\x05':'MEM_SAVE', b'\x06':'AUD_CUES', b'\x07':'ASK_USER', b'\x08':'SAVEGAME',
                b'\x10':'IF_CHECK', b'\x11':'ELSE', b'\x12':'ELSE_IFS', b'\x30':'SWITCH',
                b'\x31':'SWITCHOP', b'\x80':'GCL_SCPT', b'\xFF':'END_LINE', b'\x00':'NULL' 
}

def commandToEnglish(hex):
    try: 
        commandNamesEng[hex]
        return commandNamesEng[hex]
    except:
        return "BYTE WAS NOT DEFINED!!!!" 

def checkFreq(offsetCheck): # Checks if the next two bytes are a codec number or not. Returns True or False.
    global radioData
    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0] # INT from two bytes

    if 14000 < freq < 14200:
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
    lengthT = struct.unpack('>h', lengthBytes)[0]
    return lengthT

def getLength(offsetCheck): # Returns the length of the command, offset must be at the freq bytes
    global radioData
    
    lengthBytes = radioData[offsetCheck + 1: offsetCheck + 3]
    lengthT = struct.unpack('>H', lengthBytes)[0]
    return lengthT

def getByteAtOffset(offsetCheck): # Returns a single byte, probably redundant
    global radioData
    return radioData[offsetCheck]

def handleCallHeader(offsetCheck): # Assume call is just an 8 byte header for now
    global radioData
    global output
    header = radioData[offset: offset + 12 ]

    # Separate the header
    Freq = header[0:2]
    unk0 = header[2:4]
    unk1 = header[4:6]
    unk2 = header[6:8]
    callLength = header[9:11]
    numBytes = 0

    if header[8].to_bytes() == b'\x80':
        numBytes = struct.unpack('>h', callLength)[0]
    else:
        output.write(f'ERROR AT byte {offset}! Call length is reading as {numBytes} \n')

    # Quick check we ended with an FF
    if header[11].to_bytes() == b'\xff': 
        output.write('Call intro ended with FF successfully\n')
    else:
        output.write(f'Call header DID NOT end in FF! Check hex at {offset + 11}')

    output.write(f'Call Header: {Freq}, {unk0}, {unk1}, {unk2}, Call is {numBytes} bytes long, hex {callLength}:\n')
    return

def handleCommand(offsetCheck): # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    # global radioFile
    global radioData
    global output
    commandByte = radioData[offsetCheck].to_bytes()
    
    match commandByte:
        case b'\x00': # AKA A null
            output.write('NULL!\n')
            return offsetCheck + 1
        case b'\x01':
            output.write('Dialogue! -- ')
            length = getLength(offsetCheck)
            while radioData[offsetCheck + length + 1].to_bytes() != b'\xff':
                print(f'We have a long one at offset {offsetCheck}! Length is not FF, adding 1...\n')
                length += 1
            line = radioData[offsetCheck: offsetCheck + length + 3]
            unk1 = line[3:5]
            unk2 = line[5:7]
            unk3 = line[7:9]
            dialogue = line[9: length + 1]
            # output.write(f'Last byte in line is {line[length + 1].to_bytes()}\n') ## Should always end in FF!
            
            if b'\x80\x23\x80\x4e' in dialogue:  # this replaces the in-game hex for new line with a \\r\\n
                dialogue = dialogue.replace(b'\x80\x23\x80\x4e', b'\x5c\x72\x5c\x6e')
                output.write('Dialogue new line replaced! \n')

            if jpn:
                dialogue = translateJapaneseHex(dialogue)
                writeToFile = f'Length (int) = {length}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, UNK3 = {unk3.hex()}, Text: {str(dialogue.hex())}\n'
            else:
                writeToFile = f'Length (int) = {length}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, UNK3 = {unk3.hex()}, Text: {str(dialogue)}\n'
            # Write to file
            output.write(writeToFile)
            return offsetCheck + length + 2
        case _:
            output.write('Command is not cased! -- ')
            start = offset 
            while radioData[offsetCheck].to_bytes() != b'\xFF':
                offsetCheck += 1
            line = radioData[start : offsetCheck + 1]
            writeToFile = str(commandByte) + ": Offset: " + str(offsetCheck) + " // Content: " + str(line.hex()) + "\n\n"
            output.write(writeToFile)
            return offsetCheck + 1 

def translateJapaneseHex(bytestring):
    i = 0
    messageString = ''

    while i < len(bytestring) - 1:
        messageString += radioDict.getRadioChar(bytestring[i:i+2].hex())
        i += 2
    return messageString

if __name__ == '__main__':
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
            offset = handleCommand(offset)
    # Close output file
output.close()