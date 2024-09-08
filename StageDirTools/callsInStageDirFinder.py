import os, struct
import argparse
import json

import progressbar
bar = progressbar.ProgressBar()

# filename = "radioDatFiles/STAGE-usa-d1.DIR"

freqList = [
    b'\x37\x05', # 140.85, Campbell
    b'\x37\x10', # 140.96, Mei Ling
    b'\x36\xbf', # 140.15, Meryl
    b'\x37\x20', # 141.12, Otacon
    b'\x37\x48', # 141.52, Nastasha
    b'\x37\x64', # 141.80, Miller
    b'\x36\xE0', # 140.48, Deepthroat
    b'\x36\xb7',  # 140.07, Staff, Integral exclusive
    b'\x36\xbb',
    b'\x36\xbc', 
    bytes.fromhex('36bb'), 
    bytes.fromhex('36bc'), # 140.12, ????
    b'\x37\xac', # 142.52, Nastasha? ACCIDENT
]

# This dict will have {stageOffset: [ callOffset int, hexstr ] } to be updated later.
offsetDict: dict[int, tuple[int, str]] = {}
filesize = 0
stageData = b''

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

    writeString = f'{offset},'                                                              # Offset
    writeString += stageData[offset: offset + 4].hex() + ","                                # Frequency bytes
    writeString += str(struct.unpack('>h', stageData[offset + 1: offset + 3])[0]) + ","     # Frequency 
    callHex = str(stageData[offset + 4: offset + 8].hex()) + ","                            # offset (hex) of call in Radio.dat
    callInt = str(struct.unpack('>I', b'\x00' + stageData[offset + 5: offset + 8])[0])      # offset (int) of call in Radio.dat
    writeString += f'{callHex},{callInt},'
    writeString += "\n" # line break

    offsetDict.update({offset: (callInt, callHex)})

    output.write(writeString)

def replaceCallOffset(offset, radioOffset):
    print('This function not yet implemented!')
    # Yeah, what he said!

# For now this will just get all offsets of radio calls in the stage.dir and write a CSV file with the relevent offsets.
def getCallOffsets():
    global filesize
    global bar
    
    offset = 0
    bar.maxval = filesize
    bar.start()

    while offset < filesize:
        # Check for \x01 first, then check for a call
        if stageData[offset].to_bytes() == b'\x01' and stageData[offset + 3].to_bytes() == b'\x0a': # After running without this, seems all call offsets DO have 0x0a in the 4th byte
            if checkFreq(offset): # We only write the call to the csv if the call matches a frequency, this check might not be needed....?
                # Optional print, this is still useful for progress I guess
                # print(f'Offset {offset} has a possible call!\n====================================\n')
                writeCall(offset)
        offset += 1 # No matter what we increase offset in all scenarios
        bar.update(offset)
    bar.finish()


def main(args=None):
    global stageData
    global filesize 

    if args is None:
        args = parser.parse_args()

    # Args parsed
    filename: str = args.filename

    stageName = filename.split('/')[-2]
    stageFile = filename.split('/')[-1].split(".")[0]
    print(f'{stageName}/{stageFile}')
    
    if args.output:
        outputFile = args.output
    else:
        outputFile = f'stageAnalysis-jpn/{stageName}-{stageFile}.csv'
    
    stageDir = open(filename, 'rb')
    output = open(outputFile, 'w')

    stageData = stageDir.read() # The byte stream is better to use than the file on disk if you can. 
    filesize = len(stageData)

    # Write csv header
    output.write('offset,call hex,frequency,call data offset\n')

    # Main used to just be getting the call offsets
    getCallOffsets()
    print('Finished checking for calls in STAGE.DIR!')
    output.close()

    with open("callOffsetDict.json", 'w') as f:
        f.write(json.dumps(offsetDict))
        f.close

if __name__ == "__main__":

    # We should get args from user. Using argParse
    parser = argparse.ArgumentParser(description=f'Search a GCX file for RADIO.DAT codec calls')
    # REQUIRED
    parser.add_argument('filename', type=str, help="The GCX file to Search. Can be RADIO.DAT or a portion of it.")
    parser.add_argument('output', nargs="?", type=str, help="Output Filename (.txt)")
    
    main()

def init(filename: str):
    global filesize
    global stageData
    global output
    
    stageDir = open(filename, 'rb')
    stageData = stageDir.read()
    filesize = len(stageData)
    output = open('outputFile.txt', 'w')

    print(f'Getting STAGE.DIR call offsets... please be patient!')
    getCallOffsets()

    print('Finished checking for calls in STAGE.DIR! Ready to proceed.')
    print(f'StageDirCallFinder is Ready!')