#!/bin/python

"""
This is a quick script to pull the item description areas out of the binary. 
We're working with the japanese version, SLPM-861.11

Will add a re-injector later. For safety, will not excceed original length -1

"""

import os, struct, re, sys, json
sys.path.append(os.path.abspath('./myScripts'))
import translation.radioDict as RD

execFilename = "/home/solidmixer/projects/mgs1-undub/build-src/usa-d1/MGS/SLUS_861.11"
execFilename = "/home/solidmixer/projects/mgs1-undub/build-src/jpn-d1/MGS/SLPM_861.11"
execData = open(execFilename, 'rb').read()

outputJsonFilename = 'build-proprietary/itemDesc-jpn.json'
newDescriptionjson = 'build-proprietary/itemDesc-inject.json'

newBinaryFilename = 'build/jpn-d1/MGS/SLPM_861.11'

# Load new data
injectItemData: dict = json.load(open(newDescriptionjson, 'r'))

def getOffsets(data: bytes) -> list [tuple [int, int]]:
    offset = 0
    offsets = []
    while True:
        if execData[offset: offset + 2] != bytes.fromhex("B014") and offset < len(execData):
            offset += 2
        elif offset >= 0x2500:
            break
        else:
            endbyte = bytes.find(execData[offset:], b'\x00')
            endbyte = endbyte + (4 - (endbyte % 4))
            print(f'{struct.pack(">I", offset).hex()}: {endbyte}')
            offsets.append((offset, endbyte, execData[offset: offset + endbyte]))
            offset += endbyte
    
    return offsets

# Injection logic

if __name__ == "__main__":
    # Turn it into a list
    offsets = []
    for key in injectItemData.keys():
        print(key)
        offsets.append(int(key))
    newBinData = execData[:offsets[0]]
    # iterate through Keys... 
    for i in range(len(offsets) - 1):
        length, data = injectItemData.get(str(offsets[i]))
        injectDesc = RD.encodeJapaneseHex(data)
        if len(injectDesc[0]) > length:
            print(f'ERROR! Offset {offsets[i]} is too long! Revise... Length = {length}, currently {len(injectDesc[0])}\n{data}')
            exit(2)
        else:
            newBinData += injectDesc[0]
            newBinData += bytes(1) * (length - len(injectDesc[0]))
        if len(newBinData) == offsets[i + 1]:
            continue
        else:
            newBinData += execData[offsets[i] + length: offsets[i + 1]]
    
    # Resolve final offset:
    length, data = injectItemData.get(str(offsets[-1]))
    injectDesc = RD.encodeJapaneseHex(data)
    if len(injectDesc[0]) > length:
        print(f'ERROR! Offset {offsets[-1]} is too long! Revise...\n{data}')
        exit(2)
    else:
        newBinData += injectDesc[0]
        newBinData += bytes(1) * (length - len(injectDesc[0]))

    # Finish the file
    newBinData += execData[offsets[-1] + length: ]

    if len(newBinData) == len(execData):
        print(f'Success!! Files have same length! Outputting new binary....')
    else:
        print(f'ERROR! New binary is a different length. Please check!')
    
    with open(newBinaryFilename, 'wb') as f:
        f.write(newBinData)
        f.close
    # End!
    exit(0)


# Extractor logic

"""
if __name__ == "__main__":
    offset = 0
    offsets = getOffsets(execData[0:0x2500])

    descriptions = {}
    for item in offsets:
        descriptions.update({item[0]: [item[1], RD.translateJapaneseHex(item[2]).strip('\x00')]})
    
    with open(outputJsonFilename, 'w') as f:
        json.dump(descriptions, f, ensure_ascii=False)"""
    
