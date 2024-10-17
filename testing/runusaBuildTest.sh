#!/bin/bash

set -x

# inject Iseeeva json
# python3 myScripts/jsonTools.py recompiledCallBins/RADIO-usa-d1-Iseeva.json 

# Inject new subtitles
# python3 myScripts/xmlModifierTools.py recompiledCallBins/modifiedCalls.json recompiledCallBins/RADIO-usa-d1.xml 
python3 myScripts/xmlModifierTools.py inject recompiledCallBins/RADIO-usa-d1-Iseeva.json recompiledCallBins/RADIO-usa-d1.xml 

# Rebuild USA iso and launch in duckstation
python3 myScripts/RadioDatRecompiler.py -p -D recompiledCallBins/mergedXML.xml ./new-RADIO.DAT -s radioDatFiles/STAGE-usa-d1.DIR -S ./new-STAGE.DIR

rm build/MGS/RADIO.DAT
rm build/MGS/STAGE.DIR

mv ./new-RADIO.DAT build/MGS/RADIO.DAT
mv ./new-STAGE.DIR build/MGS/STAGE.DIR

mkpsxiso build/rebuild.xml -o mgsUSAMod.bin -c mgsUSAMod.cue -y
echo "Starting Duckstation in 2 sec!"
sleep 2

flatpak run org.duckstation.DuckStation mgsUSAMod.cue