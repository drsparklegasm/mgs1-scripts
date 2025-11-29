import os, sys, subprocess
import json
import argparse
import RadioDatTools as RDT
import DemoTools.demoSplitter as DS

# Global Variables

SETTINGS_FILE = "settings.json" # Possibly we can do it this way
ISO_PATH = "iso-extract-test/Metal Gear Solid (JPN) Disc 1.bin" # This should maybe be a runtime variable
GAME_FILES_PATH = "source"
BUILD_PATH = "build"
OUTPUT_PATH = "extracted"
EXTRACTION_TYPES = [
    "BRF",
    "DEMO",
    "FACE",
    "RADIO",
    "STAGE",
    "VOX",
    "ZMOVIE"
]

# Setup script:

def initializeStructure():
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    os.makedirs(BUILD_PATH, exist_ok=True)
    # Set up folders for each file
    for dataFileName in EXTRACTION_TYPES:
        os.makedirs(f"{OUTPUT_PATH}/{dataFileName}", exist_ok=True)

def extractISO(isoFilename: str):
    """
    For now, this will call the command line to run dumpsxiso.
    Later we can replace with manual logic.
    """
    try:
        result = subprocess.run(
            [
                'dumpsxiso', 
                '-x', GAME_FILES_PATH, 
                '-s', f'{GAME_FILES_PATH}/rebuild-{isoFilename.split("/")[-1].split('.')[0]}.xml', 
                isoFilename
                ],
            check=True)
    except:
        print(Exception)
    pass

def rebuildISO(xmlFile: str, outputFilename: str):
    try:
        result = subprocess.run(
            [
                'mkpsxiso',
                xmlFile,
                '-o', f'{outputFilename}.bin',
                '-c', f'{outputFilename}.cue'
                ],
            check=True)
    except:
        print(Exception)
    pass

def extractRadioFiles(radioFile: str, outputDir: str):
    """
    Extracts individual radio calls to folder
    """
    print(f"Extracting RADIO calls from {radioFile}...")
    args = RDT.parser.parse_args([radioFile, outputDir, '--split', '--headers' ])
    RDT.main(args)

    return

def extractDemoVoxFiles(demoFile: str, outputDir: str):
    args = DS.parser.parse_args([demoFile, outputDir])
    DS.main(args)
    return

if __name__ == "__main__":

    # Set up the working directory
    initializeStructure()

    # Example extraction
    extractISO("../iso-extract-test/Metal Gear Solid (JPN) Disc 1.bin")

    # Here we can give examples of extracting individual files to the folders
    extractRadioFiles(f"{GAME_FILES_PATH}/MGS/RADIO.DAT", f"{OUTPUT_PATH}/RADIO/")
    extractDemoVoxFiles(f"{GAME_FILES_PATH}/MGS/DEMO.DAT", f"{OUTPUT_PATH}/DEMO/")
    extractDemoVoxFiles(f"{GAME_FILES_PATH}/MGS/VOX.DAT", f"{OUTPUT_PATH}/VOX/")


    # Example rebuild
    # rebuildISO(f"{GAME_FILES_PATH}/rebuild-Metal Gear Solid (JPN) Disc 1.xml", f"{BUILD_PATH}/NewIso")