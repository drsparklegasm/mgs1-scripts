#!/bin/bash

stage_dir="radioDatFiles/stage-jpn/"

for script in $(find $stage_dir -name '*.gcx'); do
    echo $script
    python3 myScripts/StageDirTools/callsInStageDirFinder.py $script
done
