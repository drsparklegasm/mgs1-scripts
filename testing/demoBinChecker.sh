#!/bin/bash

oldBinDir="demoWorkingDir/usa/bins/"
newBinDir="demoWorkingDir/usa/newBins/"

for file in "$oldBinDir"/*; do
    BASENAME=$(basename $file)
    diff "$oldBinDir/$BASENAME" "$newBinDir/$BASENAME" 
done
