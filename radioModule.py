import RadioDatTools as RDT
import xml.etree.ElementTree as ET
import os, sys, json

class radioDataEditor():
    radioXMLData: ET.Element
    calls: list[ET.Element]
    workingCall: ET.Element
    workingVox: ET.Element
    xmlFilePath: str  # Track loaded file path for saving


    def __init__(self) -> None:
        """
        Initialize the class. Load the radio data as persistent for reading/editing.
        """
        self.radioXMLData = None
        self.calls = []
        self.workingCall = None
        self.workingVox = None
        self.xmlFilePath = None
        pass

    def loadRadioXmlFile(self, filename: str) -> None:
        try:
            self.radioXMLData = ET.parse(filename).getroot()
            self.calls = self.radioXMLData.findall("Call")
            self.xmlFilePath = filename
        except FileNotFoundError:
            print(f"Error: File not found: {filename}")
            self.radioXMLData = None
        except ET.ParseError:
            print(f"Error: Could not parse XML File {filename}. Ensure we've loaded an XML file created from RadioDatTools.")
            self.radioXMLData = None
        # Done
        return
    
    def setWorkingCall(self, offset: str):
        for call in self.calls:
            if call.get("offset") == offset:
                self.workingCall = call
                print(f'RDE: Working call was set to offset {offset}')
                break
        pass

    def setWorkingVox(self, offset: str):
        # self.workingVox = self.workingCall.find(f".//VOX_CUES[@offset='{offset}']")
        voxes = self.workingCall.findall(f".//VOX_CUES")
        for vox in voxes:
            if vox.get("offset") == offset:
                self.workingVox = vox
                print(f'VOX {offset} identified and selected')
                break
        pass
    
    def getCallOffsets(self) -> list[str]:
        """
        Returns call offsets found
        """
        callOffsets = []
        for callElem in self.calls:
            callOffsets.append(callElem.get("offset"))
        return callOffsets
    
    def getCall(self, offset: int) -> ET.Element:
        """
        Returns the call element for a given offset.
        If offset does not exist, throw error!
        """
        try:
            call = self.radioXMLData.find(f".//Call[@offset='{offset}']")
        except Exception as e:
            print(f'Error: {e}')
        return call

    def getVoxOffsets(self) -> list[str]:
        """
        Returns a list of Vox elements in the call. 
        """
        try:
            voxList = []
            audios = self.workingCall.findall(f".//VOX_CUES")
            for vox in audios:
                voxList.append(vox.get("offset"))
        except Exception as e:
            print(f'Error: {e}')
        return voxList

    def getSubs(self) -> list[str]:
        """
        Returns a list of Subtitles elements in the VOX element.
        """
        dialogue = []
        for sub in self.workingVox.findall("SUBTITLE"):
            dialogue.append(sub.get("text"))
        return dialogue

    def getSubElement(self, index: int) -> ET.Element:
        """Returns the SUBTITLE element at index within the working VOX_CUES."""
        subs = self.workingVox.findall("SUBTITLE")
        if 0 <= index < len(subs):
            return subs[index]
        return None

    def updateSubText(self, index: int, newText: str) -> None:
        """Updates the text attribute of the subtitle at index in the current VOX_CUES."""
        sub = self.getSubElement(index)
        if sub is not None:
            sub.set("text", newText)

    def addSubtitle(self, index: int, text: str, after: bool = True) -> ET.Element:
        """
        Inserts a new SUBTITLE element adjacent to the one at index.
        Copies face/anim attributes from the sibling. Returns the new element.
        """
        subs = self.workingVox.findall("SUBTITLE")
        sibling = subs[index]
        new_sub = ET.Element("SUBTITLE", {
            "offset": "0",
            "length": "0",
            "face": sibling.get("face", "95f2"),
            "anim": sibling.get("anim", "39c3"),
            "unk3": sibling.get("unk3", "0000"),
            "text": text,
            "textHex": "",
            "lengthLost": "0"
        })
        insert_pos = list(self.workingVox).index(sibling) + (1 if after else 0)
        self.workingVox.insert(insert_pos, new_sub)
        return new_sub

    def removeSubtitle(self, index: int) -> None:
        """Removes the SUBTITLE at index from the current VOX_CUES."""
        sub = self.getSubElement(index)
        if sub is not None:
            self.workingVox.remove(sub)

    def saveXML(self, filename: str) -> bool:
        """Saves the current XML tree to a file. Returns True on success."""
        try:
            tree = ET.ElementTree(self.radioXMLData)
            tree.write(filename, encoding='unicode', xml_declaration=True)
            return True
        except Exception as e:
            print(f"Error saving XML: {e}")
            return False

    def replaceVox(self, newVoxElem: ET.Element) -> None:
        """
        Replaces the modified element into the element tree (Radio Data)
        """
        pass