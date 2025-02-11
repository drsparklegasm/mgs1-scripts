#!/bin/bash

# Rebuild japanese iso and launch in duckstation

# This is the extraction area:
# /bin/python3 /home/solidmixer/projects/mgs1-undub/myScripts/RadioDatTools.py -jzx build-src/jpn-d1/MGS/RADIO.DAT radioWorkingDir/jpn-d1/RADIO-d1

# use Programatic replacement

# # Extracting and automating translation (disk 1)
# /bin/python3 /home/solidmixer/projects/mgs1-undub/myScripts/RadioDatTools.py -jzx build-src/jpn-d1/MGS/RADIO.DAT radioWorkingDir/jpn-d1/RADIO 
/bin/python3 /home/solidmixer/projects/mgs1-undub/radioWorkingDir/dialogueSwap.py

# Inject graphics data (STAGE.DIR) for disk 1 ONLY for now
wine goblin-tools/ninja.exe -i /home/solidmixer/projects/mgs1-undub/stageGraphicsWorking/jpn-d1/ -pack -o stageGraphicsWorking/out/STAGE-j1.DIR -img
# wine goblin-tools/ninja.exe -i /home/solidmixer/projects/mgs1-undub/stageGraphicsWorking/jpn-d2/ -pack -o stageGraphicsWorking/out/STAGE-j2.DIR -img 


# This area re-compiles a RADIO file for jpn
python3 myScripts/xmlModifierTools.py inject radioWorkingDir/output.json radioWorkingDir/jpn-d1/RADIO.xml 
# python3 myScripts/RadioDatRecompiler.py -p radioWorkingDir/jpn-d1/RADIO-merged.xml radioWorkingDir/jpn-d1/new-RADIO.DAT -s build-src/jpn-d1/MGS/STAGE.DIR -S radioWorkingDir/jpn-d1/new-STAGE.DIR
python3 myScripts/RadioDatRecompiler.py -p radioWorkingDir/jpn-d1/RADIO-merged.xml radioWorkingDir/jpn-d1/new-RADIO.DAT -s stageGraphicsWorking/out/STAGE-j1.DIR -S radioWorkingDir/jpn-d1/new-STAGE.DIR

# This area compiles the new DEMO.DAT and adds it to the disk image (D1)
python3 myScripts/DemoTools/demoTextInjector.py # currently hard coded
python3 myScripts/DemoTools/demoRejoiner.py  # currently hard coded

rm build/jpn-d1/MGS/RADIO.DAT
mv radioWorkingDir/jpn-d1/new-RADIO.DAT build/jpn-d1/MGS/RADIO.DAT
rm build/jpn-d1/MGS/STAGE.DIR
mv radioWorkingDir/jpn-d1/new-STAGE.DIR build/jpn-d1/MGS/STAGE.DIR
rm build/jpn-d1/MGS/DEMO.DAT
mv demoWorkingDir/jpn/new-DEMO.DAT build/jpn-d1/MGS/DEMO.DAT
# 

mkpsxiso build/jpn-d1/rebuild.xml -o mgsJpnMod-d1.bin -c mgsJpnMod-d1.cue -y
# mkpsxiso build/jpn-d2/rebuild.xml -o mgsJpnMod-d2.bin -c mgsJpnMod-d2.cue -y
flatpak run org.duckstation.DuckStation mgsJpnMod-d1.cue

