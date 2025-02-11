"""
Adapted from Green Goblins scripts. Very similar to demo
only alignments are 0x920
"""

import os, struct

version = "jpn"
filename = f"build-src/{version}-d1/MGS/ZMOVIE.STR"
outputDir = f"zMovieWorkingDir/{version}/bins"



zmFile = open(filename, 'rb')
zmData = zmFile.read()


offsets = []
os.makedirs(outputDir, exist_ok=True)

def getOffsets(toc: bytes) -> list:
    demoNum = 4 # If we figure out where this is we can implement it.
    offsets = []
    counter = 16
    for i in range(demoNum):
        offset = struct.unpack("<I", toc[counter : counter + 4])[0]
        offsets.append(offset * 0x920)
        counter += 8
    return offsets

if __name__ == "__main__":
    
    movieOffsets = getOffsets(zmData[0:0x920])
    movieOffsets.append(len(zmData))
    print(movieOffsets)

    for i in range(len(movieOffsets) - 1):
        # Write the output movie file
        with open(f'{outputDir}/{i:02}-movie.bin', 'wb') as f:
            start = movieOffsets[i]
            end = movieOffsets[i + 1]
            # Output movie data
            f.write(zmData[start : end])