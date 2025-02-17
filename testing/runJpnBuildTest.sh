#!/bin/bash

# Rebuild japanese iso and launch in duckstation
# Argument parser by chatGPT

set -e # Exit if we hit a script error.

# Parse arguments
SKIP_EXTRACTION=false
SKIP_GRAPHICS=false
SKIP_VOX=false
SKIP_DEMO=false
SKIP_RADIO=false


while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-extraction)
            SKIP_EXTRACTION=true
            shift
            ;;
        --skip-graphics)
            SKIP_GRAPHICS=true
            shift
            ;;
        --skip-vox)
            SKIP_VOX=true
            shift
            ;;
        --skip-demo)
            SKIP_DEMO=true
            shift
            ;;
        --skip-radio)
            SKIP_RADIO=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--skip-extraction] [--skip-graphics] [--skip-vox] [--skip-demo]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Graphics Injection Step
if [ "$SKIP_GRAPHICS" = false ]; then
    echo "Injecting graphics data..."
    # Inject graphics data (STAGE.DIR) for disk 1 ONLY for now
    echo "Inject D1 with ninja..."
    wine goblin-tools/ninja.exe -i /home/solidmixer/projects/mgs1-undub/workingFiles/jpn-d1/stage/ -pack -o /home/solidmixer/projects/mgs1-undub/workingFiles/jpn-d1/stage/STAGE-j1.DIR -img  >/dev/null
    # Disk 2 temp disable
    # echo "Inject D2 with ninja..."
    # wine goblin-tools/ninja.exe -i /home/solidmixer/projects/mgs1-undub/workingFiles/jpn-d2/stage/ -pack -o stageGraphicsWorking/out/STAGE-j2.DIR -img >/dev/null
    echo "New Stage.dir files created."
fi
sleep 2

# VOX Editing Step
if [ "$SKIP_VOX" = false ]; then
    echo "Processing VOX data..."
    python3 myScripts/voxTools/voxTextInjector.py
    python3 myScripts/voxTools/voxRejoiner.py
fi
sleep 2

# Demo Compilation Step
if [ "$SKIP_DEMO" = false ]; then
    echo "Compiling new DEMO.DAT..."
    python3 myScripts/DemoTools/demoTextInjector.py
    python3 myScripts/DemoTools/demoRejoiner.py
fi
sleep 2

# # Extracting and automating translation (disk 1)
# /bin/python3 /home/solidmixer/projects/mgs1-undub/myScripts/RadioDatTools.py -jzx build-src/jpn-d1/MGS/RADIO.DAT radioWorkingDir/jpn-d1/RADIO 

if [ "$SKIP_RADIO" = false ]; then
    # This area re-compiles a RADIO file for jpn
    # use Programatic replacement
    python3 /home/solidmixer/projects/mgs1-undub/build-proprietary/radio/dialogueSwap.py
    python3 myScripts/xmlModifierTools.py inject workingFiles/jpn-d1/radio/injected-Iseeva.json workingFiles/jpn-d1/radio/RADIO.xml 
    # python3 myScripts/RadioDatRecompiler.py -p radioWorkingDir/jpn-d1/RADIO-merged.xml radioWorkingDir/jpn-d1/new-RADIO.DAT -s build-src/jpn-d1/MGS/STAGE.DIR -S radioWorkingDir/jpn-d1/new-STAGE.DIR
    python3 myScripts/RadioDatRecompiler.py -p workingFiles/jpn-d1/radio/RADIO-merged.xml workingFiles/jpn-d1/radio/new-RADIO.DAT -s workingFiles/jpn-d1/stage/STAGE-j1.DIR -S workingFiles/jpn-d1/stage/new-STAGE.DIR
fi
sleep 2

echo "Moving files into position"
# Move all files into the build folder.
rm build/jpn-d1/MGS/RADIO.DAT
cp workingFiles/jpn-d1/radio/new-RADIO.DAT build/jpn-d1/MGS/RADIO.DAT -v
rm build/jpn-d1/MGS/STAGE.DIR
cp workingFiles/jpn-d1/stage/new-STAGE.DIR build/jpn-d1/MGS/STAGE.DIR -v
rm build/jpn-d1/MGS/DEMO.DAT
cp workingFiles/jpn-d1/demo/new-DEMO.DAT build/jpn-d1/MGS/DEMO.DAT -v
rm build/jpn-d1/MGS/VOX.DAT
cp workingFiles/jpn-d1/vox/new-VOX.DAT build/jpn-d1/MGS/VOX.DAT -v
# 

echo "READY TO BUILD ISO!"
sleep 2

mkpsxiso build/jpn-d1/rebuild.xml -o mgsJpnMod-d1.bin -c mgsJpnMod-d1.cue -y
# mkpsxiso build/jpn-d2/rebuild.xml -o mgsJpnMod-d2.bin -c mgsJpnMod-d2.cue -y
flatpak run org.duckstation.DuckStation mgsJpnMod-d1.cue

