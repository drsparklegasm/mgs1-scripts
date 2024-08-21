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

for input in "$input_dir"/*.xml; do
    python3 $RECOMPILESCRIPT $input 

done

for input in "$input_dir"/*.xml; do
    base_filename=$(basename "$input" .bin)
    diff $input $base_filename-mod.bin
done