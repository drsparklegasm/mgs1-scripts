#!/bin/bash

# This script runs the python script recursively, first to export all calls, then translate individual calls

SPLITSCRIPT="./myScripts/RadioDatTools.py"
RECOMPILESCRIPT="./myScripts/RadioDatRecompiler.py"
RADIODAT="radioDatFiles/RADIO-usa-d1.DAT"
input_dir='extractedCallBins'

python3 $SPLITSCRIPT $RADIODAT Headers -sH

for input in "$input_dir"/*.bin; do
    base_filename=$(basename "$input" .bin)
    output="$input_dir/$base_filename-decrypted"

    python3 $SPLITSCRIPT $input $output -xz
done

for input in "$input_dir"/*.bin; do
    python3 $RECOMPILESCRIPT $input $input_dir/$base_filename-mod.bin
    diff $input $input_dir/$base_filename-mod.bin
done
