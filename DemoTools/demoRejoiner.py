import os
import re
import glob
import struct
import progressbar
import radioTools.radioDict as RD
import json

import DemoTools.demoTextExtractor as DTE

version = "usa"
version = "jpn"

# Toggles
debug = True


# Directory configs
inputDir = f'demoWorkingDir/{version}/bins'
outputDir = f'demoWorkingDir/{version}/newBins'
outputDemoFile = f'demoWorkingDir/{version}/new-DEMO.DAT'
os.makedirs(outputDir, exist_ok=True)

origBinFiles = glob.glob(os.path.join(inputDir, '*.bin'))
origBinFiles.sort(key=lambda f: int(f.split('-')[1].split('.')[0]))

newBinFiles = glob.glob(os.path.join(outputDir, '*.bin'))
origBinFiles.sort(key=lambda f: int(f.split('-')[1].split('.')[0]))

newDemoBytes = b''

with open(outputDemoFile, 'wb') as f:
    for file in origBinFiles:
        if file.replace('bins', 'newBins') in newBinFiles:
            file = file.replace('bins', 'newBins') 
            basename = file.split("/")[-1].split(".")[0]
            print(f'Using new {basename}...')
        demoBytes = open(file, 'rb')
        newDemoBytes += demoBytes.read()
    
    f.write(newDemoBytes)
    f.close()

print(f'{outputDemoFile} was written!')

            

