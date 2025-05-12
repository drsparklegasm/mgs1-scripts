import os, sys
sys.path.append(os.path.abspath('./myScripts'))
import re
import glob
import struct
import progressbar
import translation.radioDict as RD
import json

import DemoTools.demoTextExtractor as DTE

version = "usa"
version = "jpn"
disc = 1

# Toggles
debug = True


# Directory configs
inputDir = f'workingFiles/{version}-d{disc}/demo/bins'
outputDir = f'workingFiles/{version}-d{disc}/demo/newBins'
outputDemoFile = f'workingFiles/{version}-d{disc}/demo/new-DEMO.DAT'
os.makedirs(outputDir, exist_ok=True)

origBinFiles = glob.glob(os.path.join(inputDir, '*.dmo'))
origBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

newBinFiles = glob.glob(os.path.join(outputDir, '*.dmo'))
origBinFiles.sort(key=lambda f: int(f.split('-')[-1].split('.')[0]))

newDemoBytes = b''

with open(outputDemoFile, 'wb') as f:
    for file in origBinFiles:
        if file.replace('bins', 'newBins') in newBinFiles:
            file = file.replace('bins', 'newBins') 
            basename = file.split("/")[-1].split(".")[0]
            print(f'{basename}: Using new version of the demo...')
        else:
            basename = file.split("/")[-1].split(".")[0]
            print(f'{basename}: Using old file...\r', end="")
        demoBytes = open(file, 'rb')
        newDemoBytes += demoBytes.read()
        demoBytes.close()
    f.write(newDemoBytes)
    f.close()

print(f'{outputDemoFile} was written!')

            
