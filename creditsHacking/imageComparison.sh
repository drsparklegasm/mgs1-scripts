#!/bin/bash

SCRIPT="python3 /home/solidmixer/projects/mgs1-undub/myScripts/creditsHacking/imageEncoder.py"
echo "" > creditsHacking/output/recreatedPalletes.txt

# Run the script on all the images
for file in $(ls -1 creditsHacking/output/images/*.tga); do
    echo "Running $file through script..."
    $SCRIPT $file >> creditsHacking/output/recreatedPalletes.txt
done

# Compare the blocks generated
for file in $(ls -1 creditsHacking/output/blocks/*.txt); do
    BASENAME=$(basename $file)
    if diff $file creditsHacking/output/verification/$BASENAME; then
        echo "Block $BASENAME is the same"
    else
        echo "Block $BASENAME is different"
    fi
done