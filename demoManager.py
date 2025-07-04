import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import os, sys, json

# Add subfolder(s) relative to the script location
# script_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, os.path.join(script_dir, 'radioTools'))
# sys.path.insert(0, os.path.join(script_dir, 'demoTools'))
# Assuming your submodule is in 'my-renamed-lib'
# submodule_path = os.path.join(os.path.dirname(__file__), "tools", "myscripts", "radioTools")  # Adjust path if needed
# submodule_path = os.path.join(os.path.dirname(__file__), "tools", "myscripts")  # Adjust path if needed
# sys.path.insert(0, submodule_path) # Insert at the beginning to prioritize

import demoClasses as demoCtrl
# import tools.myscripts.translation.radioDict as RD
# import tools.myscripts.translation.characters


# 
demoDatData: bytes
demoStructure: list [demoCtrl.demo]
workingDemo: demoCtrl.demo

# Testing Variables
filename = "build-src/usa-d1/MGS/DEMO.DAT"
# demoDatData = open(filename, "rb").read()
outputFilename = "workingFiles/demoDat.xml"

DEMO_HEADER: bytes = b'\x10\x08\x00\x00'
DEMO_CHUNKSIZE: int = 0x800

def findDemoOffsets(demoFileData: bytes, header: bytes, chunkSize: int):
    """
    Modified from the original splitter. This now accepts chunk size and header. 
    This should work for Demo, Vox, and Zmovie (Zmovie has different chunk size)
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

def parseDemoFile(demoDatData: bytes) -> dict [str, demoCtrl.demo]:
    demoOffsets = findDemoOffsets(demoDatData, DEMO_HEADER, DEMO_CHUNKSIZE)
    demos: dict [str, demoCtrl.demo] = {}
    for i in range(len(demoOffsets) - 1):
        demoData = demoDatData[demoOffsets[i]:demoOffsets[i + 1]]
        demos[str(demoOffsets[i])] = demoCtrl.demo(demoOffsets[i], demoData)
    demos[str(demoOffsets[-1])] = demoCtrl.demo(demoOffsets[-1], demoData)

    return demos
    # Add the final demo

if __name__ == "__main__":
    # TESTING BRANCH
    print(f'This is a test!!!')
    

    import audioTools.vagAudioTools as VAG

    # voxTestFilename = "workingFiles/usa-d1/demo/bins/demo-01.bin"
    # # voxTestFilename = "workingFiles/usa-d1/vox/bins/vox-0035.bin"
    # voxData = open(voxTestFilename, 'rb').read()
    # vox = demoCtrl.demo(demoData=voxData)
    # fileWritten = demoCtrl.outputVagFile(vox, 'demo-1', 'workingFiles/vag-examples/')
    # print(f'Wrote file: {fileWritten}')

    # jsonList = {}
    # offset, subdata = vox.toJson()
    # jsonList[offset] = subdata
    # print(jsonList)
    
    # testFile = filewritten 
    testFile = "workingFiles/vag-examples/00067.vag" 

    VAG.playVagFile(testFile)

    # # JSON output
    # jsonList = {}
    # for demo in demos:
    #     # Get demo json data here. 
    #     offset, subdata = demo.toJson()
    #     jsonList[offset] = subdata
    
    # with open("workingfiles/vag-testing.json", "w") as f:
    #     json.dump(jsonList, f, ensure_ascii=False, indent=2)
    

    """# XML Output
    allDemos = ET.Element("DemoDat")
    # allDemos.append(demos[0].structure)
    for demo in demos:
        allDemos.append(demo.structure)
        
    # TESTING BRANCH
    # testDemoExport = demos[1].structure
    xmlstr = parseString(ET.tostring(allDemos)).toprettyxml(indent="  ")
    xmlFile = open(outputFilename, 'w', encoding='utf8')
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