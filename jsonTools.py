"""
This is a collection of methods to modify json files. 

Some english calls match the japanese ones enough to zip the english lines in with the japanese offsets.
This will also help do other json modifications as needed.

"""

import os, sys, struct
import argparse
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

# import xmlModifierTools as xmlin

# flags
debug = True

# This should be the format moving forward
newjson = {
    "calls": {},
    "saves": {},
    "freqAdd": {},
    "prompts": {}
}

codecNames = {
    "メリル" : "MERYL",
    "キャンベル" : "CAMPBELL",
    "メイ・リン" : "MEI LING",
    "オタコン" : "OTACON",
    "マスター" : "MASTER",
    "ナスターシャ" : "NASTASHA",
    "ディープスロート" : "DEEPTHROAT",
}

matchingCalls = {
    "0": "0",
    "505": "910",
    
}

def replaceJsonText(callOffsetA: str, callOffsetB: str):
    """
    Replaces the subtitles in jsonB with the subtitles from jsonA while keeping the offsets the same. 
    Each Call Offset is the (original) call offset as seen in the key of the json format.
    """
    global jsonContentA
    global jsonContentB
    global newjson
    
    newCallSubs = dict(zip(jsonContentB["calls"][callOffsetB].keys(), jsonContentA["calls"][callOffsetA].values()))
    jsonContentB[callOffsetB] = newCallSubs
    newjson["calls"].update({"0": newCallSubs}) 

def writeJsonToFile(outputFilename: str):
    """
    Writes the new json file to output
    """
    global newjson

    newCall = open(outputFilename, 'w')
    newCall.write(json.dumps(newjson))
    newCall.close

# test 

"""
if __name__ == '__main__':
"""
# This one is for the whole json with all call information
"""
    parser = argparse.ArgumentParser(description=f'Zip subtitles json offsets from another. \nUsage: main.py subs.json:callOffsetA offsets.json:callOffsetB [outputFilename.json]')

    # REQUIRED
    parser.add_argument('subsJson', type=str, help="json including the subtitles we want to zip, ex: filename.json:12345")
    parser.add_argument('offsetsJson', type=str, help="json including the offsets we want to zip, ex: filename.json:12345")
    # Optionals
    parser.add_argument('output', nargs="?", type=str, help="Output Filename (.json)")

    args = parser.parse_args()
    
    subsInFilename = args.subsJson.split(':')[0]
    offsetsInFilename = args.offsetsJson.split(':')[0]

    subsCall = args.subsJson.split(':')[1]
    offsetsCall = args.offsetsJson.split(':')[1]

    jsonContentA = json.load(open(subsInFilename, 'r'))
    jsonContentB = json.load(open(offsetsInFilename, 'r'))

    matchingCalls.update({subsCall: offsetsCall})
    
    for key in matchingCalls:
        # If we need to do only one, you can do {"0": "0"}
        replaceJsonText(key, matchingCalls.get(key))
    
    outputFilename = "recompiledCallBins/modifiedCall.json"
    writeJsonToFile(outputFilename)
"""

jsonA = open("recompiledCallBins/RADIO-usa-d1-Iseeva.json", 'r')
jsonB = open("recompiledCallBins/RADIO-jpn-d1-Iseeva.json", 'r')

outputFilename = 'recompiledCallBins/modifiedCalls.json'

inputJson = json.load(jsonA)
modJson = json.load(jsonB)

# Def put calls together
for call in inputJson['calls'].keys():
    newSubs: dict = inputJson['calls'][call]
    destCall = matchingCalls.get(call)
    if destCall is None:
        continue
    newOffsets: dict = modJson['calls'][destCall]
    newCall = dict(zip(newOffsets.keys(), newSubs.values()))
    newjson['calls'][destCall] = newCall

# Save file names (Dock, heliport, etc)
# is coming out as unicode for some reason...
newSaves: dict = inputJson['saves']["38729"]
for save in modJson['saves'].keys():
    newjson['saves'][save] = newSaves

# Save options (SAVE / DO NOT SAVE)
options: dict = inputJson['prompts']["38649"]
for opt in modJson['prompts'].keys():
    newjson['prompts'][opt] = options

for name in modJson['freqAdd'].keys():
    newjson['freqAdd'][name] = codecNames.get(mod['freqAdd'].get(name))

writeJsonToFile(outputFilename)