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

jsonContentA = json.load(jsonA)
jsonContentB = json.load(jsonB)

def replaceJsonText(callOffsetA: str, callOffsetB: str):
    """
    Replaces the subtitles in jsonB with the subtitles from jsonA while keeping the offsets the same. 
    Each Call Offset is the (original) call offset as seen in the key of the json format.
    """
    global jsonContentA
    global jsonContentB
    
    newCallSubs = dict(zip(jsonContentB[callOffsetB].keys(), jsonContentA[callOffsetA].values()))
    jsonContentB[callOffsetB] = newCallSubs
    newjson = {"0": newCallSubs}

    newCall = open("14085-testing/modifiedCall.json", 'w')
    newCall.write(json.dumps(newjson))
    newCall.close

# test 



if __name__ == '__main__':
    replaceJsonText("0", "0")