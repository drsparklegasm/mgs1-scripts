# mgs1-scripts
Reverse engineering scripts for MGS1. 
So far, mostly scoped on RADIO.DAT extraction. 

# Usage

Script is VERY WORK IN PROGRESS! I'm still working on figuring out how the RADIO file is layered, and the proper lossless way to pull it.

Currently this will analyze the RADIO.DAT file and output in several ways. -H will output only the radio call headers. -x will use an XML format (all). -i will output in a json format (dialogue with offsets only). No change will output in a readable text form. 

### RadioDatTools.py

This extracts all call data, hopefully keeping other byte data intact in the file. The goal is to have all bytes there so it can be re-compiled into a new file. -h for help. This should be mostly complete now. Remaining work will be adjusting XML container data as needed for recompilation.

Usage:

```
$ RadioDatTools.py path/to/Radio.dat [outputfilename] [-h, -i, -d, ...]
```

### RadioDatRecompiler.py -- WORK IN PROGRESS
Recompiles a given XML document (exported from RadioDatTools) into a binary file. 

Eventually, it will inject the json data and recompute the lengths for all containers.

### callsInStageDirFinder.py

Since we'll hit offset problems, this script (attempts) to find all instances of a call in the stage.dir binary. There are probably a lot of false positives right now.  Logic is shamelessly reverse engineered from iseeeva's radio extractor:
https://github.com/iseeeva/metal/tree/main

### callExtractor.py

Extracts a single call based on offsets (leaves in a bin format), to be merged into a better library

### splitRadioFile.py

(WORK IN PROGRESS) This will split all calls into individual bin files with an offset name. Split files should also run properly in the main RadioDatTools.py parser script.

## Goals

1. Be able to extract all instructions and dialogue >> DONE
2. Have a readable format by another tool to adjust the dialogue and replace >> Exported to json >> DONE
3. Be able to recreate a 1:1 copy of the RADIO.DAT file when created from the tool >> IN PROGRESS
4. Be able to create a new RADIO.DAT file with translations, offsets agnostic!
5. Insert offsets into stage.dir for seamless integration, regardless of subtitle length

## Usage

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
- Work not yet started for recompiling. Need to figure out some of the if/then line ending formats
- Still missing several kanji characters that need to be OCR'd from their graphics files.
- Possibly a known mistake: 
  `ERROR! Unknown blcok at offset 1734005! Length = 11, Unknown block: 37ac2d0001ac000080075c`  
    This evaluates to 142.52, and it's a nastasha call header. Probably a mistake in the original game! Still, the conversation is a duplicate. Currently I have 142.52 as a known codec frequency which will parse the data as if this were a valid call. 