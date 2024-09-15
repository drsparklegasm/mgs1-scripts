"""
This is the modification script. It's purpose is to take an iseeeva json file and 
replace dialogue in the XML file with new dialogue. 

Afterwards it recalculates the lengths in the XML file to verify it will produce a valid RADIO.DAT file.

TODO: Figure out if we need to split jsonTools and xmlTools

CURRENTLY A WORK IN PROGRESS!

"""

failedOffsets = []
offsetFailed = False

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

root: ET.Element = None

# flags
debug = False
multithreading = True
subUseOriginalHex = False

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
    newDialogueHex = subtitleElement.get('newTextHex')
    origLength = int(subtitleElement.get('length'))
    origTextLength = int(len(subtitleElement.get('textHex')) / 2 - 1) # taking the hex and dividing by 2 and removing the trailing \x00

    if debug:
        print(f'Lengths are {int(len(newDialogueHex) / 2)} [new] and {origLength} [old], {origLength} [Element]')
    
    lengthChange = int(len(newDialogueHex) / 2) - origTextLength 
    newLength = origLength + lengthChange

    if debug:
        print(f'Previous command length: {origLength}, new length will be {newLength}')
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
    global offsetFailed
    for parent in parents:
        
        origLength = int(parent.get('length')) # length in bytes total
        origContent = parent.get('content') # 22 bytes

        if debug:
            print(f'\nEvaluating {parent.tag}...')

        match parent.tag:
            case "Call": # DONE
                # Remember length - header is 11
                newLength = origLength + lengthChange
                if (newLength - 9) > 65535:
                    print(f'CALL AT OFFSET {parent.get("offset")} HAS A LENGTH THAT IS TOO LONG! Please fix!')
                    newHexLength = "0000"
                    failedOffsets.append(parent.get("offset"))
                    offsetFailed = True
                elif (newLength - 9) < 0: 
                    print(f'CALL AT OFFSET {parent.get("offset")} HAS A LENGTH THAT IS TOO SHORT! Please fix!')
                    newHexLength = "0000"
                    failedOffsets.append(parent.get("offset"))
                    offsetFailed = True
                else:
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
                innerLength = int(parent[0].get('length')) + 2 # Get this from THEN_DO

                newLength = origLength + lengthChange
                if newLength < 65535:
                    newHexLengthA = struct.pack('>H', newLength - 2).hex() # beginning of headerz
                    newHexLengthB = struct.pack('>H', innerLength).hex() # end of line. We're assuming the THEN_DO element is already correct and stealing that length value. 
                else:
                    print(f'Offset {parent.get("offset")} has failed check!!!')
                    newHexLengthA = "0000"
                    newHexLengthB = "0000"
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
    if debug:
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
        subtitle.set('newTextHex', newText.hex())
        subtitle.set('textEscaped', "True")
        if newDict != "":
            # print(f'Dict is not Null! {newDict}')
            if newDict != callDict:
                subtitle.set('graphicsBytes', newDict)
                if debug:
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
    if debug:
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
        subtitle.set('newTextHex', newText.hex())
        subtitle.set('textEscaped', "True")
        if newDict != "":
            # print(f'Dict is not Null! {newDict}')
            if newDict != callDict:
                call.set('graphicsBytes', newDict)
                if debug:
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
        text = option.get('text')
        optLen = len(text) + 1
        option.set('length', optLen)
        innerLength += optLen + 2

    lengthBytes = struct.pack('>H', innerLength + 3).hex()
    newHeader = "ff07" + lengthBytes

    newLength = innerLength + 5
    promptElement.set("length", str(int(newLength)))
    promptElement.set("content", newHeader)
    
    return newLength - origLength

def fixCodecMem(memElement: ET.Element) -> int:
    """
    Fixes the Frequency save to codec memory.
    Returns the difference in length
    """
    origLength = int(memElement.get('length'))
    origContent = memElement.get('content')
    callName = RD.encodeJapaneseHex(memElement.get('name'))[0] # posibly add .encode('utf8')
    nameLength = len(callName)
    
    lengthBytes = struct.pack('>H', nameLength + 5).hex()
    newContent = "ff04" + lengthBytes + origContent[8:12] + callName.hex() + "00"

    newLength = nameLength + 7
    memElement.set("length", str(int(newLength)))
    memElement.set("content", newContent)
    
    return newLength - origLength

def fixSaveBlock(saveBlockElem: ET.Element) -> int:
    """
    Fixes the text that is written when saving the game.
    Returns the difference in length 
    """
    global subUseOriginalHex

    origLength = int(saveBlockElem.get('length'))
    origContent = saveBlockElem.get('content')
    
    innerLength = 0
    for option in saveBlockElem:
        lengthA = len(RD.encodeJapaneseHex(option.get('contentA'))[0]) + 1
        if subUseOriginalHex:
            lengthA = len(RD.encodeJapaneseHex(option.get('contentA'), useDoubleLength=True)[0]) + 1
        lengthB = len(option.get('contentB').encode("shift-jis")) + 1
        option.set('lengthA', str(lengthA))
        option.set('lengthB', str(lengthB))
        contlength = lengthA + lengthB + 4 # 3 bytes per save name
        option.set('length', str(contlength))
        innerLength += contlength # Each has 07{len}{content}{0x00}

    lengthBytes = struct.pack('>H', innerLength + 7).hex()  
    newHeader = "ff05" + lengthBytes + origContent[8:16]

    newLength = innerLength + 9
    saveBlockElem.set("length", str(int(newLength)))
    saveBlockElem.set("content", newHeader)
    
    return newLength - origLength

def injectSubs(jsonData: dict):
    global root
    for call in root.findall(".//Call"):
        if call.get('offset') not in jsonData["calls"].keys(): # Skip a call with no new subs to update
            continue
        newCallDialogue: dict = jsonData["calls"][call.get('offset')]
        for subelem in call.findall(".//SUBTITLE"):
            offset = subelem.get('offset')
            subelem.set('text', newCallDialogue.get(offset))
            if debug:
                print(f'Set {offset} to {newCallDialogue.get(offset)}')

def injectSaveBlocks(jsonData: dict): 
    global root

    newBlockDict = next(iter(jsonData['saves'].values()))
    for saveBlock in root.findall(".//MEM_SAVE"):
        i = 0
        for elem in saveBlock:
            newLocation = newBlockDict.get(str(i))
            elem.set("contentA", newLocation)
            elem.set("contentB", newLocation)
            i += 1

def injectCallNames(jsonData: dict):
    global root

    # inject codec mem names:
    callNames: dict = jsonData['freqAdd']
    for codecSave in root.findall(".//ADD_FREQ"):
        offset = codecSave.get('offset')
        newName = callNames.get(offset)
        codecSave.set('name', newName)

def injectUserPrompts(jsonData: dict):
    global root

    # Inject user prompts:
    prompts: dict = next(iter(jsonData['prompts'].values()))
    for promptOption in root.findall(".//ASK_USER"):
        i = 0
        for option in promptOption:
            option.set('text', prompts.get(str(i)))
            i += 1

def fixCodecMemLengths():
    global root
    # Update Save Frequency lengths (FF04) 
    print(f'Fixing codec memory names...', end="")
    i = 0
    for call in root:
        i += 1
        if debug: 
            print(f'Processing call {i}: offset: {call.get("offset")}')
        for prompt in call.findall(".//ADD_FREQ"):
            lengthChange = fixCodecMem(prompt)
            if lengthChange != 0:
                parents = getParentTree(prompt, call)
                updateParentLength(parents, lengthChange)
    print(f' Done!')

def fixPromptLengths():
    global root
    # Update Prompt lengths (FF07)
    print(f'Updating Prompt Lengths...', end="")
    i = 0
    for call in root:
        i += 1
        if debug: 
            print(f'Processing call {i}: offset: {call.get("offset")}')
        for prompt in call.findall(".//ASK_USER"):
            lengthChange = fixSavePrompt(prompt)
            if lengthChange != 0:
                parents = getParentTree(prompt, call)
                updateParentLength(parents, lengthChange)
    print(f' Done!')
    
def fixSaveBlockLengths():
    global root
    # Update Mem Save Block lengths (FF05)
    print(f'Updating Prompt Lengths...', end="")
    i = 0
    for call in root:
        i += 1
        if debug: 
            print(f'Processing call {i}: offset: {call.get("offset")}')
        for saveblock in call.findall(".//MEM_SAVE"):
            lengthChange = fixSaveBlock(saveblock)
            if lengthChange != 0:
                parents = getParentTree(saveblock, call)
                updateParentLength(parents, lengthChange)
    print(f' Done!')

def main(args=None, radioXML=None):
    global multithreading
    global debug
    global root

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
            """
            Take the input json and inject the data. 
            """
            jsonDataFile = args.input
            xmlOutputFile = args.output
            
            jsonData = json.load(open(jsonDataFile, 'r'))
            root = ET.parse(xmlOutputFile).getroot()

            injectSubs(jsonData)
            injectSaveBlocks(jsonData)
            injectCallNames(jsonData)
            injectUserPrompts(jsonData)

            outputXml = open("recompiledCallBins/mergedXML.xml", 'wb')
            xmlbytes = ET.tostring(root, encoding=None)
            outputXml.write(xmlbytes)
            outputXml.close()
            

        case 'prepare':
            xmlInputFile = args.input
            xmlOutputFile = args.output

            root = ET.parse(xmlInputFile).getroot()

            # Subtitle updates:
            if multithreading:
                print(f'Recomputing Subtitle Lengths. Please wait...')
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
            
            fixCodecMemLengths()
            fixPromptLengths()
            fixSaveBlockLengths()

            if not offsetFailed:
                outputXml = open(xmlOutputFile, 'wb')
                xmlbytes = ET.tostring(root, encoding='utf8')
                outputXml.write(xmlbytes)
                outputXml.close()
            else:
                print(f'PREP FAILED!!! The following calls exceeded the hex length of 65535 bytes:')
                print(failedOffsets)

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
    global root

    root = ET.parse(xmlInputFile).getroot()

    if multithreading:
        # Pooling mya not work because each element would have to be replaced with the element we process :|
        with Pool(processes=8) as pool:
            # Use map to process elements in parallel
            print(f'Recomputing Subtitle Lengths. Please wait...')
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
    
    fixCodecMemLengths()
    fixPromptLengths()
    fixSaveBlockLengths()
    
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