#!/bin/bash

# Rebuild japanese iso and launch in duckstation


# Here is the section to rebuild demo.dat and add it to the files. 
# python3 myScripts/DemoTools/demoTextInjector.py
# cp -n demoWorkingDir/usa/bins/* demoWorkingDir/usa/newBins/
python3 myScripts/DemoTools/demoRejoiner.py
cp demoWorkingDir/usa/new-DEMO.DAT build/usa-d1/MGS/DEMO.DAT

mkpsxiso build/usa-d1/rebuild.xml -o mgsUSAMod-d1.bin -c mgsUSAMod-d1.cue -y
# mkpsxiso build/usa-d2/rebuild.xml -o mgsUSAMod-d2.bin -c mgsUSAMod-d2.cue -y
flatpak run org.duckstation.DuckStation mgsUSAMod-d1.cue