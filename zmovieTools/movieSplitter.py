"""
Adapted from Green Goblins scripts. Very similar to demo
only alignments are 0x920
"""

import os, struct, re, sys, glob, json, argparse
sys.path.append(os.path.abspath('./myScripts'))
sys.path.append(os.path.abspath('.'))
import DemoTools.demoTextExtractor as DTE

parser = argparse.ArgumentParser(description='Split ZMOVIE.STR into individual .bin files.')
parser.add_argument('filename', type=str, help='Input ZMOVIE.STR file to split.')
parser.add_argument('output', nargs='?', type=str, help='Output directory for .bin files and extracted text.')

def getOffsets(toc: bytes) -> list:
    demoNum = 4 # If we figure out where this is we can implement it.
    offsets = []
    counter = 16
    for i in range(demoNum):
        offset = struct.unpack("<I", toc[counter : counter + 4])[0]
        offsets.append(offset * 0x920)
        counter += 8
    return offsets

def main(args=None):
    if args is None:
        args = parser.parse_args()

    filename = args.filename
    outputDir = args.output if args.output else os.path.join(os.path.dirname(os.path.abspath(filename)), '../zmovie')

    with open(filename, 'rb') as zmFile:
        zmData = zmFile.read()

    os.makedirs(os.path.join(outputDir, 'bins'), exist_ok=True)
    os.makedirs(os.path.join(outputDir, 'texts'), exist_ok=True)

    zMovieScript = {}

    movieOffsets = getOffsets(zmData[0:0x920])
    movieOffsets.append(len(zmData))
    print(movieOffsets)

    for i in range(len(movieOffsets) - 1):
        # Write the output movie file
        with open(f'{outputDir}/bins/zmovie-{i:02}.bin', 'wb') as f:
            start = movieOffsets[i]
            end = movieOffsets[i + 1]
            # Output movie data
            f.write(zmData[start : end])

    bin_files = glob.glob(os.path.join(f"{outputDir}/bins", '*.bin'))

    bin_files.sort(key=lambda f: int(f.split('/')[-1].split('-')[1].split(".")[0]))

    for bin_file in bin_files:
        with open(bin_file, 'rb') as movieTest:
            fname = os.path.basename(bin_file)
            DTE.filename = fname
            movieData = movieTest.read()

            # Get text areas
            matches = re.finditer(b'\x02\x00\x00\x00......\x10\x00', movieData, re.DOTALL)
            offsets = [match.start() for match in matches]

            # Trim false positives.
            finalMatches = []
            for offset in offsets:
                if movieData[offset + 28: offset + 32] == bytes(4):
                    finalMatches.append(offset)

            offsets = finalMatches

            texts = []
            timings = [] # list of timings (start time, duration)
            # For now we assume they are correct.
            for offset in offsets:
                length = struct.unpack("I", movieData[offset + 12 : offset + 16])[0] # Length for text only here.
                subset = movieData[offset + 16: offset + 0x7e0]
                textHexes, graphicsBytes, coords = DTE.getTextHexes(subset)
                texts.extend(DTE.getDialogue(textHexes, graphicsBytes))
                timings.extend(coords)

            basename = fname.split('.')[0]
            zMovieScript[basename] = [DTE.textToDict(texts), DTE.textToDict(timings)]
            DTE.writeTextToFile(f'{outputDir}/texts/{basename}.txt', texts)

        zMovieScript.update({basename: [DTE.textToDict(texts), DTE.textToDict(timings)]})

    with open(f'{outputDir}/zMovie-out.json', 'w') as f:
        json.dump(zMovieScript, f, ensure_ascii=False)

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
