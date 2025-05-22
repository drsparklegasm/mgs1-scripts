import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import os, sys, json

# Add subfolder(s) relative to the script location
script_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, os.path.join(script_dir, 'radioTools'))
# sys.path.insert(0, os.path.join(script_dir, 'demoTools'))
# Assuming your submodule is in 'my-renamed-lib'
submodule_path = os.path.join(os.path.dirname(__file__), "tools", "myscripts", "radioTools")  # Adjust path if needed
submodule_path = os.path.join(os.path.dirname(__file__), "tools", "myscripts")  # Adjust path if needed
sys.path.insert(0, submodule_path) # Insert at the beginning to prioritize


import DemoTools.demoClasses as demoCtrl
# import tools.myscripts.translation.radioDict as RD
# import tools.myscripts.translation.characters


# 
demoDatData: bytes
demoStructure: list [demoCtrl.demo]
workingDemo: demoCtrl.demo

# Testing Variables
filename = "../DEMO.DAT"
demoDatData = open(filename, "rb").read()
outputFilename = "demoData"

DEMO_HEADER: bytes = b'\x10\x08\x00\x00'
DEMO_CHUNKSIZE: int = 0x800

def findDemoOffsets(demoFileData: bytes, header: bytes, chunkSize: int):
    """
    Modified from the original splitter. This now accepts chunk size and header. 
    """
    offset = 0
    offsets = []
    while offset < len(demoFileData):
        checkbytes = demoFileData[offset:offset + 4]
        if checkbytes == header:
            offsets.append(offset)
            offset += chunkSize # All demo files are aligned to 0x800, SIGNIFICANTLY faster to do this than +8! Credit to Green Goblin
        else:
            offset += chunkSize
    return offsets

if __name__ == "__main__":
    # TESTING BRANCH
    print(f'This is a test!!!')
    demoOffsets = findDemoOffsets(demoDatData, DEMO_HEADER, DEMO_CHUNKSIZE)
    demos: list [demoCtrl.demo] = []
    for i in range(len(demoOffsets) - 1):
        demoData = demoDatData[demoOffsets[i]:demoOffsets[i + 1]]
        demos.append(demoCtrl.demo(demoOffsets[i], demoData))
    # Add the final demo
    demos.append(demoCtrl.demo(demoOffsets[-1], demoData))
    
    allDemos = ET.Element("DemoDat")
    # allDemos.append(demos[0].structure)
    for demo in demos:
        allDemos.append(demo.structure)
    
    jsonList = []
    for demo in demos:
        # Get demo json data here. 
        jsonList.append(demo.toJson())
    
    with open("workingfiles/testJson.json", "w") as f:
        json.dump(f, jsonList)


    """# TESTING BRANCH
    testDemoExport = allDemos[1].structure
    xmlstr = parseString(ET.tostring(testDemoExport)).toprettyxml(indent="  ")
    xmlFile = open(f'{outputFilename}.xml', 'w', encoding='utf8')
    xmlFile.write(xmlstr)
    xmlFile.close()"""


"""
    stringOut = ET.tostring(testDemoExport, encoding='utf-8')
    parseString(stringOut)
    xmlstr = stringOut.toprettyxml(indent="  ")
    # xmlstr = parseString(ET.tostring(allDemos)).toprettyxml(indent="  "
    xmlFile = open(f'{outputFilename}.xml', 'wb')
    xmlFile.write(stringOut)
    xmlFile.close()
    """