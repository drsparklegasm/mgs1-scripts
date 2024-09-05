#!/bin/bash

for script in $(find . -name '*.gcx'); do
    echo $script
    python3 myScripts/StageDirTools/callsInStageDirFinder.py $script
done
