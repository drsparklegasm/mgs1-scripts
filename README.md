# mgs1-scripts
Reverse engineering scripts for MGS1. 
So far, mostly scoped on RADIO.DAT extraction. 

# Project Goals

I started this to finally have an un-dubbed version of Metal Gear Solid to play with. Hopefully once we can inject english subtitles into the Japanese version, we'll be able to experience the original VA performance and see the subtleties between versions released in the US and JPN. 

You can find additional details on my blog at ![mgs-undubbed.io](https://blog.mgs-undubbed.io)

# Next steps:

Most of the tooling is done. There are some finishing touches for demo and zmovie still before the code is complete. Then it's onto translation. 

# Usage

Most of the scripts will have command-line based arguments. I do have some directories still hard coded. 

## Directories and Flow

Each of the files have several scripts to help with editing. I do want to explain how my scripts are used, though. Most everything has a command line usage with arguments. There are some instances where things still need to be hard coded. For that I've tried to keep all of the variables in the top section so they can be easily changed. 

The top level of my project folder looks like this:

```
[Project Folder]
├── build
│   ├── jpn-d1
│   │   ├── DUMMY3M.DAT
│   │   ├── MGS
│   │   ├── SYSTEM.CNF
│   │   ├── license_data.dat
│   │   └── rebuild.xml
│   ├── jpn-d2 ...
│   ├── usa-d1
│   └── usa-d2
├── build-proprietary
│   ├── README.md
│   ├── US Version Text.txt
│   ├── demo
│   │   ├── demoText-jpn-modified.json
│   │   └── demoText-jpn-undub.json
│   ├── itemDesc-inject.json
│   ├── itemDesc-jpn.json
│   ├── jsonCompare.py
│   ├── radio
│   │   ├── codecWindowPreview.py
│   │   ├── dialogueLineReplace.json
│   │   ├── dialogueSwap.py
│   │   ├── output.json
│   │   └── storyCalls.json
│   ├── vox
│   │   ├── vox-jpn-d1.json
│   │   └── voxText-jpn-d1.json
│   └── zmovie
├── build-src
│   ├── jpn-d1
│   │   ├── DUMMY3M.DAT
│   │   ├── MGS
│   │   ├── SYSTEM.CNF
│   │   ├── license_data.dat
│   │   └── rebuild.xml
│   ├── jpn-d2 ...
│   ├── usa-d1 ...
│   └── usa-d2 ...
├── myScripts
│   ├── DemoTools
│   ├── ... etc
├── workingFiles
```

For each of the top level directories here's my description:
- **build-src** : All original iso files and the rebuild.xml generated by dumpsxiso are written here. 
- **build** : These are the modified files that are rebuilt using mkpsxiso for testing
- **build-proprietary** : These files contain my script files that are injected. 
- **myScripts** : (this repository of code)
- **workingFiles** : I should have everything extracted by script going here. This was a recent change, not everything is there. 

The reasons I had for splitting them this way was:
1. Common file paths that could have [*version*] or [*disk*] swapped out easily.
2. This keeps an unmodified version of the disk's original contents so that i can replace it when i want to revert changes.
3. the build-proprietary folder now holds my working files so that they are not included. The scripts themselves have no copyrighted material, but as the "source" files for my modifications contain the US version texts, I wanted to make a separate git repository for both collaboration and tracking changes to my mods. 
 
Hopefully this helps wth the script, once I revisit front-end and UX, I'll look at doing a master config file so that it's clear where things are being saved. For now, my goal for each script will be to function similarly to the radioTools.py script where an input/output file is specified in the command line usage.

## Recompilation workflow

For a working example of how everything is compiled, check this script as it is what i use for running all of the scripts in tandem. 
myScripts/testing/runJpnBuildTest.sh

This script..
1. Starts with the unmodified files
2. Extracts them to the working directory
3. Modifies them with my new dialogues from build-proprietary
4. Compiles the new dat files and moves them to build/ (If something is excluded or skipped we replace it with the original)
5. Also runs any fixes (for example, stage.dir offset adjustments)
6. Compiles a new iso with mkpsxiso, and 
7. opens the resulting iso file in Duckstation for testing. 

I do want to note for testing, do not use savestates as that has led to crashes/instability for me. Use them within the same iso, don't save a state and then load it with a new build.

# The scripts 

## Radio.dat

Quick overview:

1. RadioDatTools.py -- Extract game text in xml and json format
2. xmlModifierTools.py -- Imports adjusted json dialogue into the XML file. Recomputes lengths of all calls as needed
3. RadioDatRecompiler.py -- Takes an XML Radio data and creates a .dat file. Can run the recompiler and also adjust stage.dir values (using -s and -S flags)

Most scripts have an arg parser, use -h for help.

ex: 

`RadioDatTools.py -h` for help.

```
usage: RadioDatTools.py [-h] [-v] [-i] [-s] [-H] [-g] [-x] [-z] filename [output]

Parse a binary file for Codec call GCL. Ex. script.py <filename> <output.txt>

positional arguments:
  filename         The call file to parse. Can be RADIO.DAT or a portion of it.
  output           Output Filename (.txt)

options:
  -h, --help       show this help message and exit
  -v, --verbose    Write any errors to stdout for help parsing the file
  -i, --indent     Indents container blocks, WORK IN PROGRESS!
  -s, --split      Split calls into individual bin files
  -H, --headers    Extract call headers ONLY!
  -g, --graphics   export graphics
  -x, --xmloutput  Exports the call data into XML format
  -z, --iseeeva    Exports the dialogue in a json like Iseeeva's script
  ```

## Demo.dat

Example usage:

1. splitDemoFiles.py -- Splits all demo files to individual demos
2. demoTextExtractor.py -- Extracts texts from all demo files in the output folder
3. demoTextInjector.py -- Injects json text back into demo files, outputs the binaries as new files
4. demoRejoiner.py -- Joins all demo files into one large DAT file. 

## Known issues:
- RADIO.DAT: MGS Integral does nto recompile correctly. I think there is extra null space between call data (after graphics data) that will need to be accounted for. The data is correct, but there's also too much graphics data. 
- RADIO.DAT: Recompiler works but will not correctly count/re-encode special characters. 
- RADIO.DAT: Still missing/incorrect kanji characters that need to be OCR'd from their graphics files. ~30 yet to identify, numerous others are wrong. Reach out to me if you would like to help translate them!
- RADIO.DAT: Have not tested all the offset adjustments to STAGE.DIR yet. Could be faulty. Works so far as I've tested.

This tool is now functional with some limitations:
1. Save blocks need some manual tweaks in the code to be 100% accurate on recompile, but it can be done. 
2. Length calculations should be correct. The script will warn you if a call exceeds the safe limit (length bytes are only 2, so max length in bytes of a call is 65535, if we exceed this the files may not work properly.)

# Using this script to replace the dialogue. 

To use this to make changes, run it in more or less this way... Here's an example workflow:

1. Use RadioDatTools.py to export an `XML` and `json` file containing the full data. 
```python radioDatTools.py RADIO.DAT -zx```
2. Edit the XML data. If using the json, use the jsonTools.py to inject call dialogue into XML data. Optionally use json tools to merge dialogue with offsets from different versions. 
```python jsontools.py subtitles.json offsets.json```
3. Use xmlModifierTools.py to inject the json data to the XML. Differnt aspects can be commeted out, but should match the original if untouched.
```python xmlModifierTools.py inject RADIO-output-Iseeva.json RADIO-output.xml```
4. Once the XML is fully completed, it's time to recompile RADIO.DAT. Use the radioDatRecompiler to recompile any valid XML into a binary DAT file. use the -S to modify STAGE.DIR offset numbers. There will be expected errors, but at this time it might work. If STAGE.DIR is specified (-s) we use that as a template to fix offsets and output a new file (use -S to set output name)
```python RadioDatRecompiler.py -p RADIO-output.xml new-RADIO.DAT -s STAGE.DIR -S new-STAGE.DIR```

There are nuances there but that's basically the gist. either `RadioRecompiler -p` or `xmlModifierTools prepare` will calculate the lenght changes needed. For more info, use -h on any script.

[Note: Recompiling with the -x uses the original hex for dialogue and overrides any changes, but DOES NOT RECALCULATE LENGTHS! Use it to ensure recompilation is working, not for xml files where lengths were changed.]

# Scripts Overview

## Main tools:

### RadioDatTools.py

This extracts all call data, hopefully keeping other byte data intact in the file. The goal is to have all bytes there so it can be re-compiled into a new file. -h for help. This should be mostly complete now. Remaining work will be adjusting XML container data as needed for recompilation.

Can also split calls out for further analysis.

Usage:

```
$ RadioDatTools.py path/to/Radio.dat [outputfilename] [-h, -i, -d, ...]
```

### RadioDatRecompiler.py 
Recompiles a given XML document (exported from RadioDatTools) into a binary file. 

Eventually, it will inject the json data and recompute the lengths for all containers.

### xmlModifierTools.py

Scripts to modify the XML, including recalculating lengths once dialogues have been changed. 

NOTE! It will not correctly account for any two-byte characters that were decoded!

### jsonTools.py

Use this to zip together offsets from one json and subtitles from another json (useful for injecting an English subtitle in with japanese offsets)

### StageDirTools

### callsInStageDirFinder.py

Scripts for finding all call offsets in Stage.dir. Currently this is working. Can be run on its own for analysis tools. 

Logic is shamelessly reverse engineered from iseeeva's radio extractor:
https://github.com/iseeeva/metal/tree/main

## radioTools

### callExtractor.py

Extracts a single call based on offsets (leaves in a bin format), to be merged into a better library

### callInsertor.py

Inserts a call into an existing RADIO.DAT file. Useful if you want to modify only one call's worth of binary and inject it at the original offset. Good for testing recompiler logic.

### splitRadioFile.py -- DEPRECATED

Previously split RADIO.DAT into individual calls. Use RadioDatTools with the -s option. 

### characters.py

Contains dicts in use by the radioDict library. SOME CHARACTERS HAVE YET TO BE IDENTIFIED!

### radioDict.py

The heart of the translation of japanese/special character hex. This has libraries for decoding the odd hex codes into japanese characters, but can also assist in outputting graphics found in the data. 

NOTE: Does not yet decode / re-encode all characters. 

