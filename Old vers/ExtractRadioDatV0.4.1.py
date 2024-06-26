#!/bin/python

"""
We can't get all the way through, so let's try parsing some calls.

v0.3.6: Adding a "Chunk pull" and "chunk analyzer"
v0.3.9: Removed Chunk pull
v0.4: Rebuild with FF as start of each command. 
v0.4.1: Adding main() block, in preparation for translating any file length, including subsets including a single call
"""
# Project notes
# TODO: Handle other cases, fix natashas script breaking shit (Cases)
# TODO: Mei ling scripts fucked up
# TODO: CASE switching study
# TODO: Container looping ? # IF Statements break these right now
# TODO: Change this to a library to parse on command
# TODO: Shift to export as XML
# TODO: work on recompiler

import os, struct, re
import radioDict
import argparse

## Formatting Settings!

jpn = False
indentToggle = True
debugOutput = True
filename = "RADIO-usa.DAT"
outputFilename = "Radio-decrypted.txt"

# Initalizing files
radioFile = open(filename, 'rb')
output = open(outputFilename, 'w')

# Script variables 
offset = 0
layerNum = 0
radioData = radioFile.read() # The byte stream is better to use than the file on disk if you can. 
fileSize = len(radioData)
contDepth = 0

def __init__(self, filename: str):
    radioFile = open(filename, 'rb')
    global radioData
    radioData = radioFile.read()



# A lot of this is work in progress or guessing from existing scripts
commandNamesEng = { b'\x01':'SUBTITLE',
                    b'\x02':'VOX_CUES', 
                    b'\x03':'ANI_FACE', 
                    b'\x04':'ADD_FREQ',
                    b'\x05':'MEM_SAVE', 
                    b'\x06':'MUS_CUES', 
                    b'\x07':'ASK_USER', 
                    b'\x08':'SAVEGAME',
                    b'\x10':'IF_CHECK', 
                    b'\x11':'ELSE', 
                    b'\x12':'ELSE_IFS', 
                    b'\x30':'SWITCH',
                    b'\x31':'SWITCHOP', 
                    b'\x40':'EVAL_CMD' 
                    # b'\x80':'GCL_SCPT' 
                    # b'\xFF':'CMD_HEDR',
                    # b'\x00':'NULL' 
}

def commandToEnglish(hex: bytes) -> str:
    global output
    try: 
        commandNamesEng[hex]
        return commandNamesEng[hex]
    except:
        return f'BYTE {hex.hex()} WAS NOT DEFINED!!!!'
    
def indentLines() -> None: # Purely formatting help
    if indentToggle == True:
        for x in range(layerNum):
            output.write('\t')

def checkFreq(offset: int) -> bool:  # Checks if the next two bytes are a codec number or not. Returns True or False.
    global radioData
    freq = struct.unpack('>h', radioData[offset : offset + 2])[0] # INT from two bytes
    if 14000 < freq < 14200:
        return True
    else: 
        return False
    
def getFreq(offset: int) -> float: # If freq is at offset, return frequency as 140.15
    global radioData

    freq = struct.unpack('>h', radioData[ offset : offset + 2])[0]
    return freq / 100

def getLength(offset: int) -> int: # Returns COMMAND length, offset must be at the 0xff bytes, length is bytes 1 and 2.
    global radioData
    
    lengthBytes = radioData[offset + 2: offset + 4]
    length = struct.unpack('>H', lengthBytes)[0]
    return length + 2

def getLengthManually(offset: int) -> int: # Assumes it's a header ending in 80 XX XX 
    length = 0
    while True:
        length += 1
        if radioData[offset + length].to_bytes() == b'\xff' and radioData[offset + length - 3].to_bytes() == b'\x80' and not checkFreq(offset + length):
            return length
        elif radioData[offset + length].to_bytes() == b'\xff' and radioData[offset + length - 1].to_bytes() == b'\x00' and radioData[offset + length + 1].to_bytes() in commandNamesEng:
            return length

def getCallLength(offset: int) -> int: # Returns CALL length, offset must be at the freq bytes
    global radioData

    lengthT = struct.unpack('>h', radioData[offset + 2 : offset + 4])[0]
    return lengthT

def handleCallHeader(offset: int) -> int: # Assume call is just an 8 byte header for now, then \x80, then script length (2x bytes)
    global radioData
    global output
    global layerNum
    
    # OPTIONAL Add an offset tracker output?
    
    header = 11 # Call headers are static 11
    line = radioData[ offset : offset + header ]

    # Separate the header
    humanFreq = getFreq(offset)
    unk0 = line[2:4] # face 1
    unk1 = line[4:6] # face 2
    unk2 = line[6:8] # Usually nulls
    callLength = line[9:11]
    length = struct.unpack('>h', callLength)[0]

    # Quick error checking
    if debugOutput:
        if line[8].to_bytes() != b'\x80':
            output.write(f'ERROR! AT byte {offset}!! \\x80 was not found \n') # This means what we analyzed was not a call header!
            return False

    output.write(f'\nCall Header: {humanFreq:.2f}, offset = {offset}, length = {length}, UNK0 = {unk0.hex()}, UNK1 = {unk1.hex()}, UNK2 = {unk2.hex()}, Content = {line.hex()}\n')
    layerNum += 1
    return header

def handleUnknown(offset: int) -> int: # Iterates checking frequency until we get one that is valid.... hopefully this gets us past a chunk of unknown data.
    count = 0
    output.write(f'ERROR! Unknown blcok at offset {offset}! ')
    while True:
        if checkFreq(offset + count + 1):
            break
        elif radioData[offset + count].to_bytes() == b'\xff' and radioData[offset + count + 1].to_bytes() in commandNamesEng:
            break
        else: 
            count += 1
    content = radioData[offset: offset + count]
    output.write(f'Length = {count}, Unknown block: {content.hex()}\n')
    return count

def handleCommand(offset: int) -> int: # We get through the file! But needs refinement... We're not ending evenly and lengths are too long. 
    global output
    global contDepth
    global layerNum
    # output.write(f'Offset is {offset}\n') # print for checking offset each loop
    commandByte = radioData[offset + 1].to_bytes() # Could add .hex() to just give hex digits
    """
    if radioData[offset].to_bytes() == b'\x31':
        output.write(f'ERROR! Offset for \x31 was not sent the preceeding \x00! correcting...')
        offset -= 1
        commandByte = b'\x31'
        """

    indentLines() # Indent before printing the command to our depth level.

    # We now deal with the byte
    match commandByte:

        case b'\x00': # AKA A null, May want to correct this to ending a \x02 segment
            
            output.write(f'NULL (Command! offset = {offset})\n')
            if layerNum > 0:
                layerNum -= 1
            """if radioData[offset + 1] == b'\x31':
                length = handleCommand(offset + 1)
                return length + 7"""
            return 1
        
        case b'\x01':
            length = getLength(offset) 
            line = radioData[ offset : offset + length]
            output.write('Dialogue -- ')
            # Don't do logic for extra nulls, caught in main loop.
            face = line[4:6]
            anim = line[6:8]
            unk3 = line[8:10]
            dialogue = line[10 : length]
            
            lineBreakRepace = False
            if b'\x80\x23\x80\x4e' in dialogue:  # this replaces the in-game hex for new line with a \\r\\n
                lineBreakRepace = True
                dialogue = dialogue.replace(b'\x80\x23\x80\x4e', b'\x5c\x72\x5c\x6e')

            # Write to file
            if jpn:
                dialogue = str(dialogue.hex()) # We'll translate when its working
            
            output.write(f'Offset = {offset}, Length = {length}, FACE = {face.hex()}, ANIM = {anim.hex()}, UNK3 = {unk3.hex()}, breaks = {lineBreakRepace}, \tText: {str(dialogue)}\n')
            return length
        
        case b'\x02':
            output.write('VOX START! -- ')
            header = getLengthManually(offset)
            length = getLength(offset)
            line = radioData[offset : offset + header]
            voxLength1 = struct.unpack('>h',line[2:4])[0]
            voxLength2 = struct.unpack('>h',line[9:11])[0]
            
            # Check for even length numbers
            if debugOutput:
                if voxLength1 - voxLength2 != 7:
                    print(f'ERROR!! OFFSET {offset} HAS A \\x02 that does not evenly fit!')

            output.write(f'Offset: {str(offset)}, LengthA = {voxLength1}, LengthB = {voxLength2}, Content: {str(line.hex())}\n')
            container(offset + header, length - header) # ACCOUNT FOR HEADER AND LENGTH BYTES! This may be off... too bad!
            return length
        
        case b'\x03':
            output.write('ANIMATE -- ')
            length = getLength(offset)
            line = radioData[offset : offset + length]
            containerLength = line[2:4]
            face = line[4:6]
            anim = line[6:8]
            buff = line[8:10]

            output.write(f'Offset: {str(offset)}, length = {length} FACE = {face.hex()}, ANIM = {anim.hex()}, FullContent: {str(line.hex())}\n')
            return length
        
        case b'\x04':
            output.write('ADD FREQ -- ')
            length = getLength(offset)
            line = radioData[offset : offset + length]
            containerLength = getLength(offset)
            freq = getFreq(offset + 4)
            entryName = line[6 : length - 1]

            # Just a safety since the length of this was hard-coded
            if debugOutput:
                if struct.unpack('>h', line[2:4])[0] != length - 2:
                    print(f'ERROR! Offset {offset} has an ADD_FREQ op that does not match its length!')

            output.write(f'Offset: {str(offset)}, length = {containerLength}, freqToAdd = {freq}, entryName = {entryName}, FullContent: {str(line.hex())}\n')
            return length
        
        case b'\x05':
            output.write(commandToEnglish(commandByte))
            # Content (USA): b'ff050565120000aa07098044806f8063806b0007098263828f8283828b00071180488065806c80698070806f8072807400071182678285828c82898290828f8292829400071780548061806e806b900180488061806e80678061807200071782738281828e828b814082678281828e82878281829200070980438065806c806c00070982628285828c828c000713804d80658064806990018072806f806f806d000713826c82858284828981408292828f828f828d00070d80418072806d806f8072807900070d82608292828d828f8292829900071580418072806d806f80728079900180538074806800071582608292828d828f82928299814082728294828800070d80438061806e8079806f806e00070d82628281828e8299828f828e000717804e8075806b806590018042806c8064806790018031000717826d8295828b828581408261828c828482878140825000071b804e8075806b806590018042806c80648067802e90018042803100071b826d8295828b828581408261828c8284828781448140826182500007178043806d806e80648065807290018072806f806f806d0007178262828d828e82848285829281408292828f828f828d00071b804e8075806b806590018042806c80648067802e90018042803200071b826d8295828b828581408261828c828482878144814082618251000707804c80618062000707826b82818282000709804380618076806500070982628281829682850007198055802e80478072806e80649001805080738073806780650007198274814482668292828e82848140826f82938293828782850007158043806f806d806d9001805480778072900180410007158262828f828d828d81408273829782928140826000071b8052806f806f806690168043806f806d806d900180548077807200071b8271828f828f8286815e8262828f828d828d81408273829782920007158043806f806d806d9001805480778072900180420007158262828f828d828d814082738297829281408261000715805480778072900180578061806c806c90018041000715827382978292814082768281828c828c8140826000070f80578061806c806b80778061807900070f82768281828c828b8297828182990007138053806e806f8077806680698065806c80640007138272828e828f8297828682898285828c828400071b8042806c8061807380749001804680758072806e80618063806500071b8261828c8281829382948140826582958292828e8281828382850007178043806180728067806f90018045806c80658076802e0007178262828182928287828f81408264828c82858296814400071380578061807280658068806f80758073806500071382768281829282858288828f82958293828500071b80578061807280658068806f8075807380659001804e8074806800071b82768281829282858288828f8295829382858140826d8294828800071b8055802e80478072806e8064900180428061807380659001803100071b8274814482668292828e8284814082618281829382858140825000071b8055802e80478072806e8064900180428061807380659001803200071b8274814482668292828e8284814082618281829382858140825100071b8055802e80478072806e8064900180428061807380659001803300071b8274814482668292828e828481408261828182938285814082520007138043806d806e806490018072806f806f806d0007138262828d828e828481408292828f828f828d000715805380708070806c80799001805280748065802e000715827282908290828c82998140827182948285814400071380458073806390018052806f80758074806500071382648293828381408271828f829582948285000000'
            length = 1384 # Might be US specific?
            line = radioData[offset:offset + length]
            output.write(f' -- Offset: {str(offset)}, length = {length}, FullContent: {str(line.hex())}\n')
            return length

        case b'\x06' | b'\x07' | b'\x08': 
            output.write(commandToEnglish(commandByte))
            length = getLength(offset)
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            return length

        case b'\x10': # 
            output.write(commandToEnglish(commandByte))
            length = getLength(offset)
            header = getLengthManually(offset) # Maybe not ?
            line = radioData[offset : offset + header]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            layerNum += 2
            return header
        
        case b'\x11' | b'\x12': # If, ElseIF, Else respectively
            output.write(commandToEnglish(commandByte))
            header = getLengthManually(offset) # Maybe not ?
            length = getLength(offset + header - 2)
            line = radioData[offset : offset + header]
            output.write(f' -- Offset = {offset}, length = {header}, length = {length} Content = {line.hex()}\n')
            layerNum += 1
            return header
        
        # This one is fugly. Time to look at containerizing these or something. 
        case b'\x30' | b'\x31':
            # 30 is handled different, as it has a container header
            if commandByte == b'\x30':
                length = getLengthManually(offset)
            else:
                length = 7 # Hard code this for now, works in most cases.
            line = radioData[offset : offset + length]
            output.write(commandToEnglish(commandByte))
            scriptLength = struct.unpack('>h',line[length - 2: length])[0]
            
            output.write(f' -- offset = {offset}, Script is {scriptLength} bytes, Content = {line.hex()}\n')
            return length 
        
        case b'\x40':
            output.write(commandToEnglish(commandByte))
            # The last bytes in the 0x40 expression are 14 31 00...
            length = 16
            while True:
                checkingOffset = offset + length
                if checkFreq(checkingOffset):
                    break

                if radioData[checkingOffset].to_bytes() == b'\xff' or b'\x00':
                    if radioData[checkingOffset - 3:checkingOffset] == b'\x14\x31\x00':
                        break

                length += 1
            
            line = radioData[offset : offset + length]
            output.write(f' -- Offset = {offset}, length = {length}, Content = {line.hex()}\n')
            return length
        
        case b'\xFF': # This basically menas offset should be 1 less... we'll continue processing but output will error at this offset.
            output.write(f'ERROR! Command was 0xFF at offset {offset}!!! \n')
            if debugOutput:
                print(f'ERROR! Command was 0xFF at offset {offset}!!! \n')
            length = 1
            return length

        case _:
            output.write(f'ERROR! Command is not yet cased! Command = {commandByte} -- ')
            
            length = getLengthManually(offset)
            line = radioData[offset : offset + length]
            output.write(f'Offset: {offset}, Content = {line.hex()}\n')
            return length
        

def container(offset, length): # THIS DOESNT WORK YET! We end up with recursion issues...
    counter = 0
    global layerNum
    global contDepth
    internalOffset = offset
    layerNum += 1
    while counter < length:
        if radioData[internalOffset].to_bytes() == b'\x00':
            commandLength = handleCommand(internalOffset - 1) # This is to still write a null (as an end of line) as a command.
        else:
            commandLength = handleCommand(internalOffset)
        internalOffset += commandLength
        counter += commandLength
    return length

def outputCallHeaders(filename: str):
    # Let's move this to a SplitRadioFile.py script
    return

## Translation Commands:
def translateJapaneseHex(bytestring: bytes) -> str: # Needs fixins, maybe move to separate file?
    i = 0
    messageString = ''

    while i < len(bytestring) :
        try:
            messageString += radioDict.getRadioChar(bytestring[ i : i + 2 ].hex())
        except:
            output.write(f'Unable to translate Japanese byte code {bytestring[i : i+2].hex()}!!!\n')
            messageString += '[ERROR!]'
        i += 2
        
    return messageString

def main():
    global offset
    global layerNum
    global jpn
    global indentToggle
    global debugOutput
    global fileSize

    nullCount = 0

    # Parser logic
    parser = argparse.ArgumentParser(description=f'Parse a binary file for Codec call GCL. Ex. script.py <filename> <output.txt>')

    parser.add_argument('filename', type=str, help="The call file to parse. Can be RADIO.DAT or a portion of it.")
    parser.add_argument('-o', '--output', type=str, required=False, help="(Optional) Provides an output file (.txt)")
    
    parser.add_argument('-v', '--verbose', action='store_true', help="Write any errors to stdout for help parsing the file")
    parser.add_argument('-j', '--japanese', action='store_true', help="Toggles translation for Japanese text strings")
    parser.add_argument('-i', '--indent', action='store_true', help="Indents container blocks, WORK IN PROGRESS!")
    args = parser.parse_args()

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

    radioFile = open(args.filename, 'rb')
    #radioFile = open(filename, 'rb')
    radioData = radioFile.read()
    fileSize = len(radioData)

    # END PARSING. Now onto the fun!
    """
    This is the main loop. Mostly it should just read either a frequency `3705` in two bytes, a command (`ff ??`), or a NULL (`00`)
    Unfortunately there's a lot of odd cases, so I needed to keep adding logic. We should probably clean this up at some point.

    Too bad!
    """

    while offset < fileSize - 1: # We might need to change this to Case When... as well.
        # Offset Tracking
        if debugOutput:
            print(f'Main loop: offset is {offset}')

        if nullCount == 4:
            output.write(f'ALERT!!! We just had 4x Nulls in a row at offset {offset}\n')
            nullCount = 0

        # MAIN LOGIC
        if radioData[offset].to_bytes() == b'\x00': # Add logic to tally the nulls for reading ease
            indentLines()
            if radioData[offset + 1].to_bytes() == b'\x31': # For some reason switch statements don't have an FF
                length = handleCommand(offset)
            else:
                output.write(f"Null! (Main loop) offset = {offset}\n")
                nullCount += 1
                if layerNum > 0:
                    layerNum -= 1
                length = 1
        elif radioData[offset].to_bytes() == b'\xFF': # Commands start with FF
            nullCount = 0
            length = handleCommand(offset)
        elif checkFreq(offset): # If we're at the start of a call
            nullCount = 0
            handleCallHeader(offset)
            length = 11 # In this context, we only want the header
            layerNum = 1
        else: # Something went wrong, we need to kinda reset
            length = handleUnknown(offset) # This will go until we find a call frequency
        offset += length

    output.close()

    if offset >= fileSize - 1:
        print(f'File was parsed successfully! Written to {outputFilename}')

# This doesn't work because i did not code with contextual variables in mind >:O
if __name__ == '__main__':
    # We should get args from user. Using argParse
    main()
