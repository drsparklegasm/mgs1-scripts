import os, struct

filename = "STAGE.DIR"
outputFile = "stageCalls.csv"

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
    b'\x37\x10', # 140.48, Deepthroat
    b'\x36\xb7'  # 140.07, Staff
]

def checkFreq(offset):
    global stageData
    global freqList
    for frequency in freqList:
        if stageData[offset + 1 : offset + 3] == frequency:
            return True
    
    return False

def writeCall(offset):
    global stageData
    global freqList
    global output

    writeString = str(offset) + "," + stageData[offset: offset + 4].hex() + "," 
    writeString += str(struct.unpack('>h', stageData[offset + 1: offset + 3])[0]) + "," 
    writeString += str(stageData[offset + 4: offset + 8].hex()) 
    writeString += "\n"
    output.write(writeString)


while offset < fileSize:
    # Check for \x01 first, then check for a call
    if stageData[offset].to_bytes() == b'\x01':
        if checkFreq(offset): # We only write the call to the csv if the call matches a frequency
            # Optional print, this is still useful for progress I guess
            print(f'Offset {offset} has a possible call!\n====================================\n')
            writeCall(offset)

    offset += 1 # No matter what we increase offset in all scenarios

print('Finished checking for calls in STAGE.DIR!')
output.close()