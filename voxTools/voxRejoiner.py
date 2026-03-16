import os, sys
sys.path.append(os.path.abspath('./myScripts'))
import glob
import argparse
import json

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
    newBinBasenames = {os.path.basename(f).split('.')[0] for f in newBinFiles}

    print(f'Building New VOX File...')
    newvoxBytes = b''
    newOffsets = {}  # vox number -> new byte offset hex string

    count = 0
    with open(outputvoxFile, 'wb') as f:
        for file in origBinFiles:
            basename = os.path.basename(file).split(".")[0]
            voxNum = basename.split("-")[-1]

            # Record new offset before appending
            newOffsets[voxNum] = f'{len(newvoxBytes):08x}'

            new_file_path = os.path.join(newBinsDir, f'{basename}.vox')
            if basename in newBinBasenames:
                file = new_file_path
                print(f'{basename}: Using new version...')
                count += 1
            else:
                print(f'{basename}: Using old version...\r', end="")

            with open(file, 'rb') as vf:
                newvoxBytes += vf.read()

        # If we ran out of new bins but have a source VOX.DAT, append the remainder
        if count == len(newBinFiles) and originalVox and len(origBinFiles) > 0:
            # Check if there's more data in the original VOX.DAT beyond what we've covered
            origSize = os.path.getsize(originalVox)
            if len(newvoxBytes) < origSize:
                print(f'\nAll new files injected. Using the remainder of original file...')
                with open(originalVox, 'rb') as origFile:
                    origFile.seek(len(newvoxBytes))
                    newvoxBytes += origFile.read()

        f.write(newvoxBytes)

    # Save new offsets for STAGE.DIR adjustment
    outputDir = os.path.dirname(outputvoxFile) if os.path.dirname(outputvoxFile) else '.'
    offsetsPath = os.path.join(outputDir, 'newVoxOffsets.json')
    with open(offsetsPath, 'w') as f:
        json.dump(newOffsets, f, indent=4)

    print(f'{outputvoxFile} was written!')
    print(f'New offsets saved to {offsetsPath} ({len(newOffsets)} entries)')

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
