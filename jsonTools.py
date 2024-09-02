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

jsonA = ""
jsonB = ""

def replaceJsonText(callOffsetA: int, callOffsetB: int):
    """
    Replaces the subtitles in jsonB with the subtitles from jsonA while keeping the offsets the same. 
    Each Call Offset is the (original) call offset as seen in the key of the json format.
    """
    newCallSubs = dict(zip(jsonB[callOffsetB].keys(), jsonA[callOffsetA].values()))
    jsonB[callOffsetB] = newCallSubs

if __name__ == '__main__':
    print(f'initialized.')