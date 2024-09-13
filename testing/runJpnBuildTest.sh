#!/bin/bash

# Rebuild japanese iso and launch in duckstation

echo "Injecting call jsons"
python3 myScripts/jsonTools.py 

echo "Recompute lengths"
python3 myScripts/xmlModifierTools.py inject recompiledCallBins/modifiedCalls.json recompiledCallBins/RADIO-jpn-d1.xml

echo "Recompiling RADIO.DAT and creating STAGE.DIR..."
python3 myScripts/RadioDatRecompiler.py -p recompiledCallBins/mergedXML.xml -s /radioDatFiles/STAGE-jpn-d1.DIR 

# Move radio and stage files (originals)
mv new-RADIO.DAT build-jpn/MGS/RADIO.DAT
mv new-STAGE.DIR build-jpn/MGS/STAGE.DIR

mkpsxiso build-jpn/rebuild.xml -o mgsJpnMod.bin -c mgsJpnMod.cue -y
flatpak run org.duckstation.DuckStation mgsJpnMod.cue