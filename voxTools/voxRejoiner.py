import os, sys
sys.path.append(os.path.abspath('./myScripts'))
import re
import glob
import struct
import progressbar
import radioTools.radioDict as RD
import json

import voxTools.voxTextExtractor as DTE

version = "usa"
version = "jpn"
disc = 1

# Toggles
debug = True

# Directory configs
originalVox = f'build-src/{version}-d{disc}/MGS/VOX.DAT'
inputDir = f'workingFiles/{version}-d{disc}/vox/bins'
outputDir = f'workingFiles/{version}-d{disc}/vox/newBins'
outputvoxFile = f'workingFiles/{version}-d{disc}/vox/new-VOX.DAT'
os.makedirs(outputDir, exist_ok=True)

origBinFiles = glob.glob(os.path.join(inputDir, '*.bin'))
origBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

newBinFiles = glob.glob(os.path.join(outputDir, '*.bin'))
origBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

print(f'Building New VOX File...')
newvoxBytes = b''

count = 0
with open(outputvoxFile, 'wb') as f:
    for file in origBinFiles:
        if count == len(newBinFiles):
            print(f'\nAll new files injected. Using the remainder of original file...')
            with open(originalVox, 'rb') as originalVox:
                originalVox.seek(len(newvoxBytes))
                newvoxBytes += originalVox.read()
                break
        elif file.replace('bins', 'newBins') in newBinFiles:
            file = file.replace('bins', 'newBins') 
            basename = file.split("/")[-1].split(".")[0]
            print(f'{basename}: Using new {basename}...')
            count += 1
        else:
            basename = file.split("/")[-1].split(".")[0]
            print(f'{basename}: Using old version...\r', end="")
        voxBytes = open(file, 'rb')
        newvoxBytes += voxBytes.read()
        voxBytes.close()
    f.write(newvoxBytes)
    f.close()

print(f'{outputvoxFile} was written!')

            
