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
import jsonTools

# For now we'll leave these as static for testing
xmlInputFile = "14085-testing/283744-decrypted.xml"
xmlOutputFile = "14085-testing/283744-new.xml"

"""
jsonInputFile = "extractedCallBins/usa-d1/0-decrypted-Iseeva.json"
jsonOutputFile = "extractedCallBins/textswapping-output.json"
"""

usaSubs = "extractedCallBins/usa-d1/0-decrypted-Iseeva.json"
jpnSubs = "extractedCallBins/jpn-d1/0-decrypted-Iseeva.json"

# flags
debug = True

# Open the XML tree and the json data
root = ET.parse(xmlInputFile)
newSubsData = json.load(open('14085-testing/modifiedCall.json', 'r')) 



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
    lengthElement = int(subtitleElement.attrib.get('length'))
    oldTextLength = lengthElement - 11
    # oldTextLength = int(len(subtitleElement.attrib.get('textHex')) / 2 - 1) # taking the hex and dividing by 2 and removing the trailing \x00

    if debug:
        print(f'Lengths are {len(newDialogue)} [new] and {oldTextLength} [old], {lengthElement} [Element]')
    
    lengthChange = oldTextLength - len(newDialogue) 
    commandLength = int(subtitleElement.attrib.get('length'))
    newLength = commandLength - lengthChange
    if debug:
        print(f'Previous command length: {commandLength}, new length will be {newLength}')
    if lengthChange != 0:
        subtitleElement.attrib.update({"length": str(newLength)})
    else:
        print(f'No change needed! {lengthChange}')

    return lengthChange

    # STILL NEED TO UPDATE LENGTHS ABOVE! Need a separate one for that. We will - newlength from existing each time. 

def updateParentLength(subElement: ET.Element, lengthChange: int) -> None:
    """
    Updates the length of the parent of the subtitle.

    Each case is changing the content block and length as appropriate.

    """
    parents = getParentTree(subElement)
    for parent in parents:
        match parent.tag:
            case "Call": # DONE
                # Remember length - header is 9
                origLength = int(parent.attrib.get('length')) # length in bytes total
                origContent = parent.attrib.get('content') # 22 bytes

                newLength = origLength - lengthChange
                newHexLength = struct.pack('>H', newLength - 9).hex()
                if debug:
                    print(f'New length: {newLength}')
                    print(f'Bytes before were 0x{origContent[18:22]}')
                
                newContent = origContent[0:18] + newHexLength
                if debug:
                    print(f'new content: {newContent}')

                parent.set('length', str(newLength))
                parent.set('content', newContent)

            case "VOX_CUES": # DONE
                # Remember length - header is 9
                origLength = int(parent.attrib.get('length')) # length in bytes total
                origContent = parent.attrib.get('content') # 22 bytes

                newLength = origLength - lengthChange
                newHexLengthA = struct.pack('>H', newLength - 2).hex() # beginning of headerz
                newHexLengthB = struct.pack('>H', newLength - 9).hex() # end of line

                if debug:
                    print(f'New length: {newLength}')
                    print(f'Bytes before were 0x{origContent[18:22]}')
                
                newContent = origContent[0:4] + newHexLengthA 
                newContent += origContent[8:18] + newHexLengthB
                if debug:
                    print(f'new content: {newContent}')

                parent.set('length', str(newLength))
                parent.set('content', newContent)

            case "IF_CHECK":
                # Header is variable. We just need to get the he
                origLength = int(parent.attrib.get('length')) # length in bytes total
                origContent = parent.attrib.get('content') # 22 bytes
                headerTextLength = len(origContent)
                origLengthB = struct.unpack('>H', bytes.fromhex(origContent[headerTextLength - 4: headerTextLength]))[0]

                
                if debug:
                    print(f'New length: {newLength}')
                    print(f'Header before was 0x{origContent}')

                newLength = origLength - lengthChange
                newHexLengthA = struct.pack('>H', newLength - 2).hex() # beginning of headerz
                newHexLengthB = struct.pack('>H', origLengthB - lengthChange).hex() # end of line

                if debug:
                    print(f'New length: {newLength}')
                    print(f'Bytes before were 0x{origContent[18:22]}')
                
                newContent = origContent[0:2] + newHexLengthA + origContent[ 4 : headerTextLength - 4 ] + newHexLengthB
                if debug:
                    print(f'new content: {newContent}')

                parent.set('length', str(newLength))
                parent.set('content', newContent)

            case "THEN_DO": # DONE
                # No actual hex in here, we just need to modify the length for posterity
                origLength = int(parent.attrib.get('length')) # length in bytes total
                newLength = origLength - lengthChange

                if debug:
                    print(f'Old length: {origLength} | New length: {newLength}')
                    
                parent.set('length', str(newLength))
                
            case "ELSE":
                print('stuff')
            case "ELSE_IFS":
                print('stuff')
            case "RND_SWCH":
                print('stuff')
            case "RND_OPTN":
                print('stuff')
            case "RadioData":
                return
            case _:
                print(f'We fucked up! Tried to update length of {parent.tag}!!!')
            
    return

def getParentTree(target: ET.Element) -> list:
    """
    Credit goes to chatGPT, we need to iterate through and get each parent along the way.
    """
    path = []
    for parent in root.iter():
        for element in parent:
            if element == target:
                path.append(parent)
                path.extend(getParentTree(parent))
                break

    return path

def insertSubs(jsonInputFile: str, callOffset: int):
    """
    Replaces subs in the element with the new values. 
    Uses xmlInputFile as root (Element Tree) and jsonInputFile (json dict)
    """
    global root
    inputJson = json.load(open(jsonInputFile, 'r'))

    for callOffset in newSubsData:
        callElement = root.find(f".//Call[@offset='{callOffset}']")
        newSubs = newSubsData[callOffset]
        for key in newSubs:
            subElement = callElement.find(f".//SUBTITLE[@offset='{key}']")
            if debug:
                print(f'Old Text = {subElement.attrib.get("text")}')
                print(f'New Text = {newSubs[key]}')

            subElement.set('text', newSubs.get(key))
            if debug:
                print(ET.tostring(subElement))

# Helpful shit for analysis and planning
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
"""
usaSubs = "14085-testing/293536-decrypted-Iseeva.json"
jpnSubs = "14085-testing/283744-decrypted-Iseeva.json"

jsonA = json.load(open(usaSubs, 'r'))
jsonB = json.load(open(jpnSubs, 'r'))

jsonTools.replaceJsonText("0", "0")
text = json.dumps(jsonB)

if debug:
    print(text)

with open("14085-testing/modifiedCall.json", 'w') as f:
    f.write(text)
    f.close()
    
"""

insertSubs('14085-testing/modifiedCall.json', '283744')

for subtitle in root.findall(f".//SUBTITLE"):
    lengthChange = updateLengths(subtitle, 0)
    parents = getParentTree(subtitle)
    print(parents)
    updateParentLength(subtitle, lengthChange)


outputXml = open(xmlOutputFile, 'w')
xmlstr = ET.tostring(root.getroot(), encoding="unicode")
outputXml.write(f'{xmlstr}')
outputXml.close()