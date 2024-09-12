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
from multiprocessing import Pool
from radioTools import radioDict as RD
# import jsonTools

import progressbar
bar = progressbar.ProgressBar()

"""
jsonInputFile = "extractedCallBins/usa-d1/0-decrypted-Iseeva.json"
jsonOutputFile = "extractedCallBins/textswapping-output.json"
"""

usaSubs = "extractedCallBins/usa-d1/0-decrypted-Iseeva.json"
jpnSubs = "extractedCallBins/jpn-d1/0-decrypted-Iseeva.json"

# flags
debug = False
multithreading = True

# Open the XML tree and the json data
# newSubsData = json.load(open('14085-testing/modifiedCall.json', 'r')) 

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
    newDialogue = subtitleElement.get('text')
    lengthElement = int(subtitleElement.attrib.get('length'))
    oldTextLength = lengthElement - 11
    # oldTextLength = int(len(subtitleElement.attrib.get('textHex')) / 2 - 1) # taking the hex and dividing by 2 and removing the trailing \x00

    if debug:
        print(f'Lengths are {len(newDialogue)} [new] and {oldTextLength} [old], {lengthElement} [Element]')
    
    lengthChange = len(newDialogue) - oldTextLength 
    commandLength = int(subtitleElement.get('length'))
    newLength = commandLength + lengthChange
    if debug:
        print(f'Previous command length: {commandLength}, new length will be {newLength}')
    if lengthChange != 0:
        subtitleElement.set("length", str(newLength))
    #else:
    #    print(f'No change needed! {lengthChange}')

    return lengthChange

    # STILL NEED TO UPDATE LENGTHS ABOVE! Need a separate one for that. We will - newlength from existing each time. 

def updateParentLength(parents: list[ET.Element], lengthChange: int) -> None:
    """
    Updates the length of the parent of the subtitle.
    Each case is changing the content block and length as appropriate.

    """
    for parent in parents:
        
        origLength = int(parent.get('length')) # length in bytes total
        origContent = parent.get('content') # 22 bytes

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
                # Header is variable. We just need to get the hex
                headerTextLength = len(origContent)
                origLengthB = int(parent[0].get('length')) + 2 # Get this from THEN_DO

                newLength = origLength + lengthChange
                newHexLengthA = struct.pack('>H', newLength - 2).hex() # beginning of headerz
                newHexLengthB = struct.pack('>H', origLengthB).hex() # end of line. We're assuming the THEN_DO element is already correct and stealing that length value. 
                newContent = origContent[0:4] + newHexLengthA + origContent[ 8 : headerTextLength - 4 ] + newHexLengthB

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
            print(f'{parent.get("offset")}: Old length: {origLength}, New length: {newLength}, change is {lengthChange}')
            # print(f"Old Content: {origContent}")
            # print(f"New Content: {newContent}")

    return

def getParentTree(target: ET.Element, root: ET.Element) -> list:
    """
    Credit goes to chatGPT, we need to iterate through and get each parent along the way.
    Modified to accept the call element as the root. Its not like we need the RadioData element.
    """
    path = []
    for parent in root.iter():
        for element in parent:
            if element == target:
                path.append(parent)
                path.extend(getParentTree(parent, root))
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

def processSubtitle(call: ET.Element):
    # Inefficient. We need to speed this up. 
    count = 0
    numSubtitles = len(call.findall('.//SUBTITLE'))
    print(f'Call offset: {call.get("offset")}, Compiling {numSubtitles} subtitles...')

    for subtitle in call.findall(f".//SUBTITLE"):
        count += 1
        # Get all parent elements:
        # parents = getParentTreeThreaded(subtitle, root)
        parents = getParentTree(subtitle, call)
        print(f"\rSubtitle {count} of {numSubtitles} Offset: {subtitle.get('offset')} / {call.get('offset')}: ", end="")
        # Re-encode two-byte characters
        callDict: str = parents[-1].get('graphicsBytes')
        newText, newDict = RD.encodeJapaneseHex(subtitle.get('text'), callDict)

        # textString = repr(newText)
        textString = newText.decode('utf8', errors='backslashreplace')
        # print(f'{subtitle.get("offset")}\n{textString}:{len(textString)}\n{textString2}:{len(textString2)}\n')

        subtitle.set('text', textString)
        subtitle.set('textEscaped', "True")
        if newDict != "":
            # print(f'Dict is not Null! {newDict}')
            if newDict != callDict:
                subtitle.set('graphicsBytes', newDict)
                print(f'Added Dict to call')

        # Update the lengths for this subtitle
        lengthChange = updateLengths(subtitle)
        
        # print(parents)
        updateParentLength(parents, lengthChange)
    # Comment out the return if needed for the first option. 
    return call

def processSubtitleThreaded(call: ET.Element, root: ET.Element) -> ET.Element:
    count = 0
    numSubtitles = len(call.findall('.//SUBTITLE'))
    print(f"Call {call.get('offset')} - Compiling {numSubtitles} subtitles...")
    
    for subtitle in call.findall(f".//SUBTITLE"):
        count += 1
        # Get all parent elements:
        parents = getParentTree(subtitle, call)
        # Re-encode two-byte characters
        callDict: str = call.get('graphicsBytes')
        newText, newDict = RD.encodeJapaneseHex(subtitle.get('text'), callDict)

        #textString = repr(newText)
        textString = newText.decode('utf8', errors='backslashreplace')
        #print(f'{subtitle.get("offset")}\n{textString}\n{textString2}\n')

        # subtitle.set('text', newText.decode('utf8', errors='backslashreplace'))
        subtitle.set('text', textString)
        subtitle.set('textEscaped', "True")
        if newDict != "":
            # print(f'Dict is not Null! {newDict}')
            if newDict != callDict:
                call.set('graphicsBytes', newDict)
                print(f'Added Dict to call')

        # Update the lengths for this subtitle
        lengthChange = updateLengths(subtitle)
        
        # print(parents)
        updateParentLength(parents, lengthChange)
    # Comment out the return if needed for the first option. 
    return call

def fixSavePrompt(promptElement: ET.Element) -> int:
    """
    Fixes the prompt text (if needed) and updates all lengths.
    Returns the difference in length
    """
    origLength = int(promptElement.get('length'))
    
    innerLength = 0
    for option in promptElement:
        innerLength += int(option.get('length'))
    lengthBytes = struct.pack('>H', innerLength + 3).hex()
    newHeader = "ff07" + lengthBytes

    newLength = innerLength + 2
    promptElement.set("length", str(int(newLength)))
    promptElement.set("content", newHeader )
    
    return newLength - origLength

def fixCodecMem(memElement: ET.Element) -> int:
    """
    Fixes the Frequency save to codec memory.
    Returns the difference in length
    """
    origLength = int(memElement.get('length'))
    origContent = memElement.get('content')
    origCallName = memElement.get('name')
    
    lengthBytes = struct.pack('>H', len(origCallName) + 7).hex()
    newContent = "ff04" + lengthBytes + origContent[8:12] + RD.encodeJapaneseHex(origCallName)[0].hex() + "00"

    newLength = len(newContent) / 2
    memElement.set("length", str(int(newLength)))
    memElement.set("content", newContent )
    
    return newLength - origLength

def fixSaveBlock(saveBlockElem: ET.Element) -> int:
    """
    Fixes the text that is written when saving the game.
    Returns the difference in length 
    """
    origLength = int(saveBlockElem.get('length'))
    origContent = saveBlockElem.get('content')
    
    innerLength = 0
    for option in saveBlockElem:
        contLength = len(option.get('contentA')) * 2 # x2 for two bytes per character TODO: Check this on recompiler
        innerLength += (contLength + 3) * 2 # Each has 07{len}{content}{0x00}
    lengthBytes = struct.pack('>H', innerLength + 7).hex()  
    newHeader = "ff05" + lengthBytes + origContent[8:16]

    newLength = innerLength + 2
    saveBlockElem.set("length", str(int(innerLength + 2)))
    saveBlockElem.set("content", newHeader)
    
    return newLength - origLength

def main(args=None, radioXML=None):
    global multithreading
    global debug

    if args == None:
        args = parser.parse_args()

    # Flags:
    if args.debug:
        debug = True
        multithreading = False
    
    if not args.input:
        args.operation = 'help'
    
    match args.operation:
    
        case "help" | "Help" | "HELP" | "hELP" | "H":
            print(f"Usage: xmlOps.py <operation> [input] [output] : \n\tinject = import json [input] with subtitles and inject them into an XML [output]\n\tprepare = Encode custom characters, recalculate lengths, prepare the file for. [XML Radio file is input, output is a new file]")
            exit(0)
        
        case "inject":
            print(f'Unfinished!')
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

        case 'prepare':

            xmlInputFile = args.input
            xmlOutputFile = args.output

            """# For now we'll leave these as static for testing
            xmlInputFile = "recompiledCallBins/RADIO-goblin.xml"
            xmlOutputFile = "recompiledCallBins/RADIO-goblin-encode.xml"""

            root = ET.parse(xmlInputFile).getroot()

            # Subtitle updates:
            if multithreading:
                # Pooling may not work because each element would have to be replaced with the element we process :|
                with Pool(processes=8) as pool:
                    # Use map to process elements in parallel
                    listOfCalls = [(call, root) for call in root]
                    modifiedCalls = pool.starmap(processSubtitleThreaded, listOfCalls)
                    for i, call in enumerate(modifiedCalls):
                        root[i] = call # This replaces the work done into the original root object. 
            else:
                count = 0
                numCalls = len(root.findall('Call'))
                for call in root:
                    count += 1
                    print(f'\nProcessing call {count} of {numCalls}')
                    processSubtitle(call)
            
            # Update Save Frequency lengths (FF04) 
            print(f'Fixing call frequency saves [NOT IMPLEMENTED]')
            count = 0
            for call in root:
                i += 1
                print(f'Processing call {i}: offset: {call.get("offset")}')
                for prompt in call.findall(".//ADD_FREQ"):
                    lengthChange = fixCodecMem(prompt)
                    if lengthChange != 0:
                        parents = getParentTree(prompt, call)
                        updateParentLength(parents, lengthChange)
            
            # Update Prompt lengths (FF07)
            print(f'Updating Prompt Lengths...')
            count = 0
            for call in root:
                i += 1
                print(f'Processing call {i}: offset: {call.get("offset")}')
                for prompt in call.findall(".//ASK_USER"):
                    lengthChange = fixSavePrompt(prompt)
                    if lengthChange != 0:
                        parents = getParentTree(prompt, call)
                        updateParentLength(parents, lengthChange)
            
            # Update Mem Save Block lengths (FF05)
            print(f'Updating Prompt Lengths...')
            count = 0
            for call in root:
                i += 1
                print(f'Processing call {i}: offset: {call.get("offset")}')
                for saveblock in call.findall(".//MEM_SAVE"):
                    lengthChange = fixSaveBlock(saveblock)
                    if lengthChange != 0:
                        parents = getParentTree(saveblock, call)
                        updateParentLength(parents, lengthChange)
            
            # Update Save Info (FF05)

            outputXml = open(xmlOutputFile, 'wb')
            xmlbytes = ET.tostring(root, encoding=None)
            outputXml.write(xmlbytes)
            outputXml.close()

        case _:
            print(f"Usage: xmlOps.py <operation> [input] [output] : \n\tinject = import json [input] with subtitles and inject them into an XML [output]\n\tprepare = Encode custom characters, recalculate lengths, prepare the file for. [XML Radio file is input, output is a new file]")
            exit(0)

def init(xmlInputFile: str) -> ET.Element:
    """
    This is to finalize encoding. Assumes all strings are in the file. 
    Recalculates all lengths and updates dictionaries. 
    Returns the finished ET "root" element.
    """
    global multithreading 

    root = ET.parse(xmlInputFile).getroot()

    if multithreading:
        # Pooling mya not work because each element would have to be replaced with the element we process :|
        with Pool(processes=8) as pool:
            # Use map to process elements in parallel
            listOfCalls = [(call, root) for call in root]
            modifiedCalls = pool.starmap(processSubtitleThreaded, listOfCalls)
            for i, call in enumerate(modifiedCalls):
                root[i] = call # This replaces the work done into the original root object.
    
    return root

if __name__ == "__main__":
    # Parse arguments here, then run main so that this can be called from another parent script.
    parser = argparse.ArgumentParser(description=f'Bulk subtitle modifier for an extracted XML RADIO file. inject subtitles or calculate it for recompilation')
    parser.add_argument('operation', type=str, help="Input XML to be recompiled. Ex: inject, prepare.")
    parser.add_argument('input', nargs="?", type=str, help="inject: Input json | prepare: input XML file")
    # This isn't elegant, we may want to just include the recompiler here. 
    parser.add_argument('output', nargs="?", type=str, help="inject: Target XML file we are modifying | prepare: Output XML file to be re-compiled.")
    # THIS IS HANDLED BY RECOMPILER ?
    parser.add_argument('-r', '--recompile', nargs="?", type=str, help="recompiles the XML into binary once finished. Only valid if running prepare")
    parser.add_argument('-v', '--debug', action='store_true', help="Prints debug information for troubleshooting compilation. NOTE: Also disables multithreading! WILL BE SLOW!")

    # Parse arguments

    main()