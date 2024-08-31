"""
This is the modification script. It's purpose is to take an iseeeva json file and 
replace dialogue in the XML file with new dialogue. 

Afterwards it recalculates the lengths in the XML file to verify it will produce a valid RADIO.DAT file.

CURRENTLY A WORK IN PROGRESS!

"""

import os, sys
import argparse
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

# For now we'll leave these as static for testing
xmlInputFile = "RADIO-usa-d1-output.xml"
xmlOutputFile = "recompiledCallBins/0-mod.xml"
jsonInputFile = "RADIO-usa-d1-output-Iseeva.json"

# flags
debug = True

# Open the XML tree and the json data
root = ET.parse(xmlInputFile)
newSubsData = json.load(open(jsonInputFile, 'r')) 

def loadNewSubs(callOffset: str) -> dict:
    """
    Gets the call subtitles for a given offset. Offset needs to come in as a string to match against the dict.
    """
    global newSubsData
    return newSubsData[callOffset]

def insertSubs():
    """
    Replaces subs in the element with the new values
    """
    global root
    global newSubsData

    for callOffset in newSubsData:
        callElement = root.find(f".//Call[@Offset='{callOffset}']")
        newSubs = newSubsData[callOffset]
        for key in newSubs:
            subElement = callElement.find(f".//SUBTITLE[@offset='{key}']")
            if debug:
                print(f'Old Text = {subElement.attrib.get("text")}')
                print(f'New Text = {newSubs[key]}')

            subElement.set('text', newSubs.get(key))
            if debug:
                print(ET.tostring(subElement))

def updateLengths(subtitleElement: ET.Element):
    """
    Fixes the length of the subtitle element after length was adjusted.
    # Subtitles need 11 added. Header is something like this:
    # (FF01) (Length 2 bytes) (95f2) (39c3) (0000) (Text) (0x00), total added = 11 bytes
    """
    
# Output the file in the same way
if __name__ == "__main__":
    insertSubs()
    root.write(xmlOutputFile, encoding='utf-8', xml_declaration=True)

"""with open(xmlOutputFile, 'wb') as f:
    xmlbytes = ET.tostring(root, encoding='utf-8')
    f.write(xmlbytes)"""