import RadioDatTools as RDT
import xml.etree.ElementTree as ET
import os, sys, json

class radioDataEditor():
    radioXMLData: ET.Element
    calls: list[ET.Element]
    workingCall: ET.Element
    workingVox: ET.Element


    def __init__(self) -> None:
        """
        Initialize the class. Load the radio data as persistent for reading/editing.
        """
        self.radioXMLData = None
        self.calls = []
        self.workingCall = None
        self.workingVox = None
        pass

    def loadRadioXmlFile(self, filename: str) -> None:
        try:
            self.radioXMLData = ET.parse(filename).getroot()
            self.calls = self.radioXMLData.findall("Call")
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

    def getVoxOffsets(self):
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

    def getSubs(self) -> list:
        """
        Returns a list of Subtitles elements in the VOX element. 
        """
        dialogue = []
        for sub in self.workingVox.findall("SUBTITLE"):
            dialogue.append(sub.get("text"))
        return dialogue

    def replaceVox(newVoxElem: ET.Element) -> None:
        """
        Replaces the modified element into the element tree (Radio Data)
        """
        pass