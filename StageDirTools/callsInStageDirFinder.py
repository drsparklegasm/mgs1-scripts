import os, struct

filename = "Radio dat files/STAGE-usa-d1.DIR"
# filename = "STAGE-jpn.DIR" # Uncomment this line if using jpn version, only changes the output csv filename

outputFile = "stageCalls-usa.csv"
if 'jpn' in filename:
    outputFile = "stageCalls-jpn.csv"

stageDir = open(filename, 'rb')
output = open(outputFile, 'w')

# Write csv header
output.write('offset,call hex,frequency,call data offset\n')

stageData = stageDir.read() # The byte stream is better to use than the file on disk if you can. 
fileSize = stageData.__len__()
offset = 0

freqList = [
    b'\x37\x05', # 140.85, Campbell
    b'\x37\x10', # 140.96, Mei Ling
    b'\x36\xbf', # 140.15, Meryl
    b'\x36\xb7', # 141.12, Otacon
    b'\x37\x48', # 141.52, Natasha
    b'\x37\x64', # 141.80, Miller
    b'\x36\xE0', # 140.48, Deepthroat
    b'\x36\xb7'  # 140.07, Staff
]

def checkFreq(offset):
    global stageData
    
    if stageData[offset + 1 : offset + 3] in freqList:
        return True
    else:
        return False

def writeCall(offset):
    global stageData
    global freqList
    global output

    writeString = str(offset) + ","                                                         # Offset, 
    writeString = stageData[offset: offset + 4].hex() + ","                                 # Frequency bytes
    writeString += str(struct.unpack('>h', stageData[offset + 1: offset + 3])[0]) + ","     # Frequency 
    writeString += str(stageData[offset + 4: offset + 8].hex()) + ","                       # offset of radio.dat call data
    writeString += str(struct.unpack('>I', b'\x00' + stageData[offset + 5: offset + 8])[0]) # Int of the offset, need 4 bytes for that
    writeString += "\n" # line break
    output.write(writeString)

def replaceCallOffset(offset, radioOffset):
    print('This function not yet implemented!')
    # Yeah, what he said!

# For now this will just get all offsets of radio calls in the stage.dir and write a CSV file with the relevent offsets.
def getCallOffsets():
    offset = 0
    while offset < fileSize:
        # Check for \x01 first, then check for a call
        if stageData[offset].to_bytes() == b'\x01' and stageData[offset + 3].to_bytes() == b'\x0a': # After running without this, seems all call offsets DO have 0x0a in the 4th byte
            if checkFreq(offset): # We only write the call to the csv if the call matches a frequency, this check might not be needed....?
                # Optional print, this is still useful for progress I guess
                print(f'Offset {offset} has a possible call!\n====================================\n')
                writeCall(offset)
        offset += 1 # No matter what we increase offset in all scenarios



# Main used to just be getting the call offsets
getCallOffsets()
print('Finished checking for calls in STAGE.DIR!')
output.close()

