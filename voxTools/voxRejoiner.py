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
inputDir = f'workingFiles/{version}-d{disc}/vox/bins'
outputDir = f'workingFiles/{version}-d{disc}/vox/newBins'
outputvoxFile = f'workingFiles/{version}-d{disc}/vox/new-VOX.DAT'
os.makedirs(outputDir, exist_ok=True)

origBinFiles = glob.glob(os.path.join(inputDir, '*.bin'))
origBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

newBinFiles = glob.glob(os.path.join(outputDir, '*.bin'))
origBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

newvoxBytes = b''

with open(outputvoxFile, 'wb') as f:
    for file in origBinFiles:
        if file.replace('bins', 'newBins') in newBinFiles:
            file = file.replace('bins', 'newBins') 
            basename = file.split("/")[-1].split(".")[0]
            print(f'Using new {basename}...')
        else:
            basename = file.split("/")[-1].split(".")[0]
            print(f'Using old {basename}...')
        voxBytes = open(file, 'rb')
        newvoxBytes += voxBytes.read()
        voxBytes.close()
    f.write(newvoxBytes)
    f.close()

print(f'{outputvoxFile} was written!')

            
