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

jsonA = open("14085-testing/38411-decrypted-Iseeva.json", 'r')
jsonB = open("14085-testing/59333-decrypted-Iseeva.json", 'r')

newjson: json = {}

matchingCalls = {}

def replaceJsonText(callOffsetA: str, callOffsetB: str):
    """
    Replaces the subtitles in jsonB with the subtitles from jsonA while keeping the offsets the same. 
    Each Call Offset is the (original) call offset as seen in the key of the json format.
    """
    global jsonContentA
    global jsonContentB
    global newjson
    
    newCallSubs = dict(zip(jsonContentB[callOffsetB].keys(), jsonContentA[callOffsetA].values()))
    jsonContentB[callOffsetB] = newCallSubs
    newjson["0"] = newCallSubs 

def writeJsonToFile(outputFilename: str):
    """
    Writes the new json file to output
    """
    global newjson

    newCall = open(outputFilename, 'w')
    newCall.write(json.dumps(newjson))
    newCall.close

# test 


if __name__ == '__main__':
    """
    This one is for the whole json with all call information
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
    
    outputFilename = "14085-testing/modifiedCall.json"
    writeJsonToFile(outputFilename)
