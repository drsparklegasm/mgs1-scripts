import struct, json
import os, sys
from progressbar import ProgressBar

# WARNING!!! FOR NOW THIS SCRIPT IS DESTRUCTIVE!!!!

bar = ProgressBar()

# Necessary files
oldOffsetFile = "workingFiles/jpn-d1/demo/bins/offsets.json"
newOffsetFile = "workingFiles/jpn-d1/demo/newDemoOffsets.json"
stageFile = "workingFiles/jpn-d1/stage/STAGE-j1.DIR"
# stageFileSrc = "build-src/jpn-d1/MGS/STAGE.DIR"
# WARNING!!! FOR NOW THIS SCRIPT IS DESTRUCTIVE!!!!

debug = False

# Global Variables
origOffsets = {}
newOffsets = {}

def importOffsets(filename: str) -> dict:
    """
    Use this to load the offsets directly to the dict object
    """
    with open(filename, "r") as f:
        offsets: dict = json.load(f)
    return offsets

if __name__ == "__main__":
    # ADDING A FINAL WARNING THAT THE SCRIPT IS DESTRUCTIVE!
    confirm = input("WARNING!!! FOR NOW THIS SCRIPT IS DESTRUCTIVE!!!!\nChanges to the STAGE.DIR file selected will be\nPERMENANT as we overwrite the original file.\n\nType \"CONFIRM\" to continue!\n> ")
    if confirm != "CONFIRM":
        exit(0)
    
    # First we need a dictionary of all stages and their new offsets.
    origOffsets = importOffsets(oldOffsetFile)
    newOffsets = importOffsets(newOffsetFile)
    offsetsToChange = {}
    # Optionally we could do a new dict where the key of original hex 
    for key in origOffsets.keys():
        # Zip together the values (hex strings) for each
        offsetsToChange.update({origOffsets.get(key):newOffsets.get(key)})
    
    # Grab stagedata
    stageData = bytearray(open(stageFile, "rb").read())
    bar.maxval = len(stageData)
    print(f"Adjusting Stage.DIR DEMO offsets...")
    offset = 0
    count = 0
    patternA: bytes = bytes.fromhex("5073060a")
    patternB: bytes = bytes.fromhex("50700408")
    bar.start()
    while offset < len(stageData):
        # if stageData[offset:offset + 4] == patternA: 
        # This one ignores second half of the pattern; we get less matches if we use pattern B. Let's go conservative first. Can change this later. 
        if stageData[offset:offset + 4] == patternA and stageData[offset + 8:offset + 12] == patternB:
            count += 1
            foundOffset = stageData[offset + 4:offset + 8]
            # Quick sanity check:
            if foundOffset.hex() in offsetsToChange.keys():
                # Set the bytes to the new offset
                stageData[offset + 4:offset + 8] = bytes.fromhex(offsetsToChange.get(foundOffset.hex()))
                if debug: print(f'{offset}: Replaced found {foundOffset.hex()} with {offsetsToChange.get(foundOffset.hex())}')
                offset += 12
                continue
            elif foundOffset.hex() == "ffffffff":
                if debug: print(f'{offset}: FFFFFFFF offset found, Skipping...')
                offset += 12
            else:
                if debug: print(f"{offset}: Patterns found but offset is NOT valid!\n{stageData[offset:offset + 12].hex(sep=" ", bytes_per_sep=4)}")
                offset += 12
        else:
            offset += 1
            # if offset % 0x10000 == 0:
            #     print(offset)
        bar.update(offset)
    # End of script. Write new stage.dir file.
    bar.finish()
    print(f"Script end! Replaced {count} offsets! Writing to disk...")
    with open(stageFile, 'wb') as out:
        out.write(stageData)
        print(f'Adjusted STAGE.DIR file: {stageFile}')
    exit(0)