import os, sys
sys.path.append(os.path.abspath('./myScripts'))
import re
import glob
import struct
import argparse
import progressbar
import translation.radioDict as RD
import json

import voxTools.voxTextExtractor as DTE

parser = argparse.ArgumentParser(description='Rejoin .vox bin files into VOX.DAT')
parser.add_argument('input', type=str, help='Input directory containing original .vox bin files.')
parser.add_argument('output', type=str, help='Output VOX.DAT file path.')
parser.add_argument('-s', '--source', nargs='?', type=str, help='Path to original VOX.DAT (used as fallback when new bins are exhausted).')
parser.add_argument('-n', '--new-bins', nargs='?', type=str, help='Directory containing new/modified .vox files. Defaults to <input>/../newBins.')

# Toggles
debug = True

def main(args=None):
    if args is None:
        args = parser.parse_args()

    inputDir = args.input
    outputvoxFile = args.output
    originalVox = args.source
    newBinsDir = args.new_bins if args.new_bins else os.path.join(inputDir, '../newBins')

    os.makedirs(os.path.dirname(outputvoxFile) if os.path.dirname(outputvoxFile) else '.', exist_ok=True)

    origBinFiles = glob.glob(os.path.join(inputDir, '*.vox'))
    origBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

    newBinFiles = glob.glob(os.path.join(newBinsDir, '*.vox'))
    newBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

    print(f'Building New VOX File...')
    newvoxBytes = b''

    count = 0
    with open(outputvoxFile, 'wb') as f:
        for file in origBinFiles:
            if count == len(newBinFiles):
                if originalVox:
                    print(f'\nAll new files injected. Using the remainder of original file...')
                    with open(originalVox, 'rb') as origFile:
                        origFile.seek(len(newvoxBytes))
                        newvoxBytes += origFile.read()
                break
            new_file_path = os.path.join(newBinsDir, os.path.basename(file))
            if new_file_path in newBinFiles:
                file = new_file_path
                basename = os.path.basename(file).split(".")[0]
                print(f'{basename}: Using new {basename}...')
                count += 1
            else:
                basename = os.path.basename(file).split(".")[0]
                print(f'{basename}: Using old version...\r', end="")
            voxBytes = open(file, 'rb')
            newvoxBytes += voxBytes.read()
            voxBytes.close()
        f.write(newvoxBytes)

    print(f'{outputvoxFile} was written!')

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
