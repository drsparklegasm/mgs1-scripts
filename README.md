# mgs1-scripts
Reverse engineering scripts for MGS1


# Usage

Script is VERY WORK IN PROGRESS! I'm still working on figuring out how the RADIO file is layered, and the proper lossless way to pull it.

### ExtractRadioDatV0.4.py

This extracts all call data, hopefully keeping other byte data intact in the file. The goal is to have all bytes there so it can be re-compiled into a new file

### callsInStageDirFinder.py

Since we'll hit offset problems, this script (attempts) to find all instances of a call in the stage.dir binary. There are probably a lot of false positives right now.  Logic is shamelessly reverse engineered from iseeeva's radio extractor:
https://github.com/iseeeva/metal/tree/main

### callExtractor.py

Extracts a single call based on offsets (leaves in a bin format)

### splitRadioFile.py

(WORK IN PROGRESS) This will split all calls into individual bin files with an offset name.

## Goals

1. Be able to extract all instructions and dialogue
2. Have a readable format by another tool to adjust the dialogue and replace
3. Be able to recreate a 1:1 copy of the RADIO.DAT file when created from the tool 

## Usage

Run it? It's not gonna get very far. Prior / testing versions are in the old version folder. 

