import os, sys
sys.path.append(os.path.abspath('./myScripts'))
import re
import glob
import struct
import argparse
import progressbar
import translation.radioDict as RD
import json

import DemoTools.demoTextExtractor as DTE

parser = argparse.ArgumentParser(description='Rejoin .dmo bin files into DEMO.DAT')
parser.add_argument('input', type=str, help='Input directory containing original .dmo bin files.')
parser.add_argument('output', type=str, help='Output DEMO.DAT file path.')
parser.add_argument('-n', '--new-bins', nargs='?', type=str, help='Directory containing new/modified .dmo files. Defaults to <input>/../newBins.')
parser.add_argument('-d', '--offset-dump', nargs='?', type=str, help='Path to save offset JSON dump.')

# Toggles
debug = True

def main(args=None):
    if args is None:
        args = parser.parse_args()

    inputDir = args.input
    outputDemoFile = args.output
    newBinsDir = args.new_bins if args.new_bins else os.path.join(inputDir, '../newBins')
    offsetDump = args.offset_dump if args.offset_dump else os.path.join(os.path.dirname(outputDemoFile), 'newDemoOffsets.json')

    os.makedirs(os.path.dirname(outputDemoFile) if os.path.dirname(outputDemoFile) else '.', exist_ok=True)

    origBinFiles = glob.glob(os.path.join(inputDir, '*.dmo'))
    origBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

    newBinFiles = glob.glob(os.path.join(newBinsDir, '*.dmo'))
    newBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

    newDemoBytes = b''
    newOffsets = {}
    with open(outputDemoFile, 'wb') as f:
        for file in origBinFiles:
            new_file_path = os.path.join(newBinsDir, os.path.basename(file))
            if new_file_path in newBinFiles:
                file = new_file_path
                basename = os.path.basename(file).split(".")[0]
                print(f'{basename}: Using new version of the demo...')
            else:
                basename = os.path.basename(file).split(".")[0]
                print(f'{basename}: Using old file...\r', end="")
            demoNum = basename.split("-")[1]
            demoStart = struct.pack(">L", len(newDemoBytes) // 0x800).hex()
            newOffsets.update({demoNum: demoStart})
            with open(file, 'rb') as demoBytes:
                newDemoBytes += demoBytes.read()

        f.write(newDemoBytes)

    print(f'{outputDemoFile} was written!')

    with open(offsetDump, 'w') as f:
        json.dump(newOffsets, f)

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
