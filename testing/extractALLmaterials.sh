#!/bin/bash

# This is the extraction area:
# /bin/python3 /home/solidmixer/projects/mgs1-undub/myScripts/RadioDatTools.py -jzx build-src/jpn-d1/MGS/RADIO.DAT radioWorkingDir/jpn-d1/RADIO-d1

# VOX editing here!

# This area compiles the new DEMO.DAT and adds it to the disk image (D1)

# # Extracting and automating translation (disk 1)
# /bin/python3 /home/solidmixer/projects/mgs1-undub/myScripts/RadioDatTools.py -jzx build-src/jpn-d1/MGS/RADIO.DAT radioWorkingDir/jpn-d1/RADIO 

# This area re-compiles a RADIO file for jpn

# Move all files into the build folder.

mkpsxiso build/jpn-d1/rebuild.xml -o mgsJpnMod-d1.bin -c mgsJpnMod-d1.cue -y
# mkpsxiso build/jpn-d2/rebuild.xml -o mgsJpnMod-d2.bin -c mgsJpnMod-d2.cue -y
flatpak run org.duckstation.DuckStation mgsJpnMod-d1.cue

