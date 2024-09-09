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
from radioTools import radioDict as RD
import jsonTools
"""import progressbar

bar = progressbar.ProgressBar()"""



"""
jsonInputFile = "extractedCallBins/usa-d1/0-decrypted-Iseeva.json"
jsonOutputFile = "extractedCallBins/textswapping-output.json"
"""

usaSubs = "extractedCallBins/usa-d1/0-decrypted-Iseeva.json"
jpnSubs = "extractedCallBins/jpn-d1/0-decrypted-Iseeva.json"

# flags
debug = False

# Open the XML tree and the json data
newSubsData = json.load(open('14085-testing/modifiedCall.json', 'r')) 

def loadNewSubs(callOffset: str) -> dict:
    """
    Gets the call subtitles for a given offset. Offset needs to come in as a string to match against the dict.
    """
    global newSubsData
    return newSubsData[callOffset]

def updateLengths(subtitleElement: ET.Element): # This MUST be a SUBTITLE element!
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
    
    lengthChange = len(newDialogue) - oldTextLength 
    commandLength = int(subtitleElement.attrib.get('length'))
    newLength = commandLength + lengthChange
    if debug:
        print(f'Previous command length: {commandLength}, new length will be {newLength}')
    if lengthChange != 0:
        subtitleElement.attrib.update({"length": str(newLength)})
    #else:
    #    print(f'No change needed! {lengthChange}')

    return lengthChange

    # STILL NEED TO UPDATE LENGTHS ABOVE! Need a separate one for that. We will - newlength from existing each time. 

def updateParentLength(subElement: ET.Element, lengthChange: int) -> None:
    """
    Updates the length of the parent of the subtitle.
    Each case is changing the content block and length as appropriate.

    """
    parents = getParentTree(subElement)
    for parent in parents:
        
        if parent.tag != 'RadioData':
            origLength = int(parent.attrib.get('length')) # length in bytes total
            origContent = parent.attrib.get('content') # 22 bytes

        if debug:
            print(f'\nEvaluating {parent.tag}...')

        match parent.tag:
            case "Call": # DONE
                # Remember length - header is 11
                newLength = origLength + lengthChange
                newHexLength = struct.pack('>H', newLength - 9).hex()

                newContent = origContent[0:18] + newHexLength

                parent.set('length', str(newLength))
                parent.set('content', newContent)

            case "VOX_CUES": # DONE
                # Remember length - header is 9
                newLength = origLength + lengthChange
                newHexLengthA = struct.pack('>H', newLength - 2).hex() # beginning of headerz
                newHexLengthB = struct.pack('>H', newLength - 9).hex() # end of line
                
                newContent = origContent[0:4] + newHexLengthA 
                newContent += origContent[8:18] + newHexLengthB

                parent.set('length', str(newLength))
                parent.set('content', newContent)

            case "IF_CHECK":
                # Header is variable. We just need to get the he
                headerTextLength = len(origContent)
                origLengthB = struct.unpack('>H', bytes.fromhex(origContent[headerTextLength - 4: headerTextLength]))[0]

                newLength = origLength + lengthChange
                newHexLengthA = struct.pack('>H', newLength - 2).hex() # beginning of headerz
                newHexLengthB = struct.pack('>H', origLengthB + lengthChange).hex() # end of line
                newContent = origContent[0:2] + newHexLengthA + origContent[ 4 : headerTextLength - 4 ] + newHexLengthB

                parent.set('length', str(newLength))
                parent.set('content', newContent)

            case "THEN_DO": # DONE
                # No actual hex in here, we just need to modify the length for posterity
                newLength = origLength + lengthChange     
                parent.set('length', str(newLength))
                
            case "ELSE":
                # Else is simple because it has no conditions to eval
                newLength = origLength + lengthChange
                headerTextLength: int = len(origContent) # 10 characters
                origLengthHex: int = struct.unpack('>H', bytes.fromhex(origContent[headerTextLength - 4: headerTextLength]))[0]
                newHexLength: bytes = struct.pack('>H', origLengthHex + lengthChange).hex() # end of line
                
                newContent = origContent[0:6] + newHexLength
                    
                parent.set('length', str(newLength))
                parent.set('content', str(newContent))

            case "ELSE_IFS":
                # FF1230 {1 byte length of eval} {eval} 80 {2 byte length}
                newLength = origLength + lengthChange
                headerTextLength: int = len(origContent) 
                origLengthHex: int = struct.unpack('>H', bytes.fromhex(origContent[headerTextLength - 4: headerTextLength]))[0]
                newHexLength: bytes = struct.pack('>H', origLengthHex + lengthChange).hex() # end of line
                
                newContent = origContent[0:headerTextLength - 4] + newHexLength
                    
                parent.set('length', str(newLength))
                parent.set('content', str(newContent))
                
            case "RND_SWCH":
                # FF30 {length} { 2 byte Probability total}
                newLength = origLength + lengthChange
                headerTextLength: int = len(origContent) # 10 characters
                origLengthHex: int = struct.unpack('>H', bytes.fromhex(origContent[ 4 : 8]))[0]
                newHexLength: bytes = struct.pack('>H', origLengthHex + lengthChange).hex() # end of line

                newContent = origContent[0:4] + newHexLength + origContent[8:headerTextLength]

                parent.set('length', str(newLength))
                parent.set('content', str(newContent))

            case "RND_OPTN":
                # {31} {2 byte probability} 80 {2b Length}
                newLength = origLength + lengthChange
                headerTextLength: int = len(origContent) 
                origLengthHex: int = struct.unpack('>H', bytes.fromhex(origContent[headerTextLength - 4: headerTextLength]))[0]
                newHexLength: bytes = struct.pack('>H', origLengthHex + lengthChange).hex() # end of line
              
                newContent = origContent[0:headerTextLength - 4] + newHexLength
                   
                parent.set('length', str(newLength))
                parent.set('content', str(newContent))

            case "RadioData":
                return
            
            case _:
                print(f'We fucked up! Tried to update length of {parent.tag}!!!')
        
        if debug:
            print(f'Old length: {origLength}, New length: {newLength}, change is {lengthChange}')
            # print(f"Old Content: {origContent}")
            # print(f"New Content: {newContent}")

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

if __name__ == "__main__":
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

    # For now we'll leave these as static for testing
    xmlInputFile = "recompiledCallBins/RADIO-goblin.xml"
    xmlOutputFile = "recompiledCallBins/RADIO-goblin-encode.xml"
    root = ET.parse(xmlInputFile)


    # insertSubs('14085-testing/modifiedCall.json', '0') # 285449

    for subtitle in root.findall(f".//SUBTITLE"):
        # Get all parent elements:
        parents = getParentTree(subtitle)
        print(f'Offset: {subtitle.get('offset')}')
        # Re-encode two-byte characters
        callDict: str = parents[-2].get('graphicsBytes')
        newText, newDict = RD.encodeJapaneseHex(subtitle.get('text'), callDict)

        subtitle.set('text', newText.decode('utf8', errors='backslashreplace'))
        if newDict != "":
            # print(f'Dict is not Null! {newDict}')
            if newDict != callDict:
                subtitle.set('graphicsBytes', newDict)
                print(f'Added Dict to call')

        # Update the lengths for this subtitle
        lengthChange = updateLengths(subtitle)
        
        # print(parents)
        updateParentLength(subtitle, lengthChange)


    outputXml = open(xmlOutputFile, 'w')
    xmlstr = ET.tostring(root.getroot(), encoding="unicode")
    outputXml.write(f'{xmlstr}')
    outputXml.close()