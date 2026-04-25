import os, sys
import json

jsonData = json.load(open('recompiledCallBins/RADIO-jpn-d1-Iseeva.json', 'r'))

with open('callDialogue.csv', 'w') as f:
    f.write(f'offset, dialogue\n')
    for callKey in jsonData["calls"].keys():
        callVox: dict = jsonData["calls"][callKey]
        for voxKey in callVox:
            voxSubs: dict = callVox[voxKey]
            for subKey in voxSubs:
                f.write(f'{subKey},{voxSubs[subKey]}\n')
    
    f.close()