"""
This is the modification script. It's purpose is to take an iseeeva json file and 
replace dialogue in the XML file with new dialogue. 

Afterwards it recalculates the lengths in the XML file to verify it will produce a valid RADIO.DAT file.

TODO: Figure out if we need to split jsonTools and xmlTools

CURRENTLY A WORK IN PROGRESS!

"""

import os, sys, struct
import argparse
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

# For now we'll leave these as static for testing
xmlInputFile = "radioDatFiles/RADIO-jpn-d2.xml"
xmlOutputFile = "recompiledCallBins/0-mod.xml"
jsonInputFile = "extractedCallBins/usa-d1/0-decrypted-Iseeva.json"
jsonOutputFile = "extractedCallBins/textswapping-output.json"

usaSubs = "extractedCallBins/usa-d1/0-decrypted-Iseeva.json"
jpnSubs = "extractedCallBins/jpn-d1/0-decrypted-Iseeva.json"

# flags
debug = True

# Open the XML tree and the json data
root = ET.parse(xmlInputFile)
newSubsData = json.load(open(jsonInputFile, 'r')) 

jsonA = json.load(open(usaSubs, 'r'))
jsonB = json.load(open(jpnSubs, 'r'))

def loadNewSubs(callOffset: str) -> dict:
    """
    Gets the call subtitles for a given offset. Offset needs to come in as a string to match against the dict.
    """
    global newSubsData
    return newSubsData[callOffset]

def updateLengths(subtitleElement: ET.Element, length: int): # NOT YET IMPLEMENTED!
    """
    Fixes the length of the subtitle element after length was adjusted.
    # Subtitles need 11 added. Header is something like this:
    # (FF01) (Length 2 bytes) (95f2) (39c3) (0000) (Text) (0x00), total added = 11 bytes
    """
    newDialogue = subtitleElement.attrib.get('text')
    oldTextLength = int(len(subtitleElement.attrib.get('textHex')) / 2 - 1) # taking the hex and dividing by 2 and removing the trailing \x00
    if debug:
        print(f'Lengths are {len(newDialogue)} [new] and {oldTextLength} [old]')
    
    lengthChange = oldTextLength - len(newDialogue) 
    commandLength = int(subtitleElement.attrib.get('length'))
    newLength = commandLength - lengthChange
    if debug:
        print(f'Previous command length: {commandLength}, new length will be {newLength}')
    if lengthChange != 0:
        subtitleElement.attrib.update({"length": str(newLength)})
    else:
        print(f'No change needed! {lengthChange}')

    # STILL NEED TO UPDATE LENGTHS ABOVE! Need a separate one for that. We will - newlength from existing each time. 

def insertSubs(jsonInputFile: str, callOffset: int):
    """
    Replaces subs in the element with the new values. 
    Uses xmlInputFile as root (Element Tree) and jsonInputFile (json dict)
    """
    global root
    inputJson = json.load(open(usaSubs, 'r'))

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

def replaceJsonText(callOffsetA: int, callOffsetB: int):
    """
    Replaces the subtitles in jsonB with the subtitles from jsonA while keeping the offsets the same. 
    Each Call Offset is the (original) call offset as seen in the key of the json format.
    """
    newCallSubs = dict(zip(jsonB[callOffsetB].keys(), jsonA[callOffsetA].values()))
    jsonB[callOffsetB] = newCallSubs

def printRadioXMLStats():
    """
    This is just to get analytical data for working with the files.
    """
    # This code just outputs the call offset and freq, mostly for me to ID them.
    xmlList = [
        "RADIO-usa-d1.xml",
        "RADIO-usa-d2.xml",
        "RADIO-jpn-d1.xml",
        "RADIO-jpn-d2.xml"
        ]

    for filename in xmlList:
        root = ET.parse(f'radioDatFiles/{filename}')
        with open(f"CallInfoResearch/callInfo-{filename}.csv", 'w') as f:
            f.write(f'Call,offsetHex,Freq,numSubtitles\n')
            for call in root.findall(f".//Call"):
                offset = call.attrib.get("Offset")
                offsetHex = struct.pack('>L', int(offset)).hex()
                freq = call.attrib.get("Freq")
                subs = len(call.findall(f".//SUBTITLE"))
                f.write(f'{offset},0x{offsetHex},{float(freq):.2f},{subs}\n')
            f.close()


# All of this is to test replacing the 140.85 call
usaSubs = "radioDatFiles/RADIO-usa-d1-Iseeva.json"
jpnSubs = "radioDatFiles/RADIO-jpn-d1-Iseeva.json"

jsonA = json.load(open(usaSubs, 'r'))
jsonB = json.load(open(jpnSubs, 'r'))

replaceJsonText("293536", "283744")
text = jsonB['283744']
if debug:
    print(text)



"""
with open("modifiedCall.json", 'w') as f:
    f.write(text)
    f.close()
"""

"""
insertSubs()
for subtitle in root.findall(f".//SUBTITLE"):
    updateLengths(subtitle, 0)

text = root.write(xmlOutputFile, encoding='utf-8', xml_declaration=True)
print(text)
"""
