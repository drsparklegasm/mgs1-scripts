import os, sys
import json

jsonData = json.load(open('recompiledCallBins/RADIO-jpn-d1-Iseeva.json', 'r'))

with open('callDialogue.csv', 'w') as f:
    f.write(f'offset, dialogue\n')
    for key in jsonData["calls"].keys():
        callDict: dict = jsonData["calls"][key]
        for key in callDict:
            f.write(f'{key},{callDict.get(key)}\n') 
    
    f.close()