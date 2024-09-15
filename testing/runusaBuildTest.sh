#!/bin/bash

# Rebuild USA iso and launch in duckstation
python3 myScripts/RadioDatRecompiler.py -p recompiledCallBins/RADIO-usa-d1.xml new-RADIO.DAT -s radioDatFiles/STAGE-usa-d1.DIR

mkpsxiso build/rebuild.xml -o mgsUSAMod.bin -c mgsUSAMod.cue -y
echo "Starting Duckstation in 5 sec!"
sleep 5

flatpak run org.duckstation.DuckStation mgsUSAMod.cue