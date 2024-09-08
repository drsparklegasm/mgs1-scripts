# mgs1-scripts
Reverse engineering scripts for MGS1. 
So far, mostly scoped on RADIO.DAT extraction. 

# Project Goals

I started this to finally have an un-dubbed version of Metal Gear Solid to play with. Hopefully once we can inject english subtitles into the Japanese version, we'll be able to experience the original VA performance and see the subtleties between versions released in the US and JPN. Here are the project milestones (mostly for Radio.dat so far)

1. Be able to extract all instructions and dialogue >> DONE
2. Have a readable format by another tool to adjust the dialogue and replace >> Exported to json >> DONE
3. Be able to recreate a 1:1 copy of the RADIO.DAT file when created from the tool >> DONE!
4. Be able to create a new RADIO.DAT file with translations, offsets agnostic! >> TESTING
5. Insert offsets into stage.dir for seamless integration, regardless of subtitle length

# Usage

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

## Known issues:
- MGS Integral does nto recompile correctly. I think there is extra null space between call data (after graphics data) that will need to be accounted for. 
- Recompiler works but will not correctly count/re-encode special characters. 
- Still missing several kanji characters that need to be OCR'd from their graphics files. ~72-80 remain. Reach out to me if you would like to help translate them!
- Have not tested the offset adjustments to STAGE.DIR yet. Could be faulty.

This tool is now functional with some limitations:
1. Re-encoding byte data will not accout for ANY special characters yet, which means lengths will be off. 
2. Length calculations across the call have not been fully tested. 

To use this to make changes, run it in more or less this way:

1. Use RadioDatTools.py to export an XML and json file containing the full data. 
2. Edit the XML data. If using the json, use the jsonTools.py to inject call dialogue into XML data
3. Use xmlModifierTools.py to re-calculate all lengths for new dialogues.
4. Once the XML is fully completed, it's time to recompile RADIO.DAT. Use the radioDatRecompiler to recompile any valid XML into a binary DAT file. use the -S to modify STAGE.DIR offset numbers. There will be expected errors, but at this time it might work. 

[Note: Recompiling with the -x uses the original hex for dialogue and overrides any changes, but DOES NOT RECALCULATE LENGTHS! Use it to ensure recompilation is working, not for xml files where lengths were changed.]

# Scripts Overview

## RadioDatTools.py

This extracts all call data, hopefully keeping other byte data intact in the file. The goal is to have all bytes there so it can be re-compiled into a new file. -h for help. This should be mostly complete now. Remaining work will be adjusting XML container data as needed for recompilation.

Can also split calls out for further analysis.

Usage:

```
$ RadioDatTools.py path/to/Radio.dat [outputfilename] [-h, -i, -d, ...]
```

## RadioDatRecompiler.py 
Recompiles a given XML document (exported from RadioDatTools) into a binary file. 

Eventually, it will inject the json data and recompute the lengths for all containers.

## xmlModifierTools.py

Scripts to modify the XML, including recalculating lengths once dialogues have been changed. 

NOTE! It will not correctly account for any two-byte characters that were decoded!

## jsonTools.py

Use this to zip together offsets from one json and subtitles from another json (useful for injecting an English subtitle in with japanese offsets)

## StageDirTools

## callsInStageDirFinder.py

Scripts for finding all call offsets in Stage.dir. Currently this is working. Can be run on its own for analysis tools. 

Logic is shamelessly reverse engineered from iseeeva's radio extractor:
https://github.com/iseeeva/metal/tree/main

# radioTools

## callExtractor.py

Extracts a single call based on offsets (leaves in a bin format), to be merged into a better library

## callInsertor.py

Inserts a call into an existing RADIO.DAT file. Useful if you want to modify only one call's worth of binary and inject it at the original offset. Good for testing recompiler logic.

## splitRadioFile.py -- DEPRECATED

Previously split RADIO.DAT into individual calls. Use RadioDatTools with the -s option. 

## characters.py

Contains dicts in use by the radioDict library. SOME CHARACTERS HAVE YET TO BE IDENTIFIED!

## radioDict.py

The heart of the translation of japanese/special character hex. This has libraries for decoding the odd hex codes into japanese characters, but can also assist in outputting graphics found in the data. 

NOTE: Does not yet decode / re-encode all characters. 

