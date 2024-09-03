#!/bin/bash

# This script runs the python script recursively, first to export all calls, then translate individual calls

SCRIPT="./myScripts/RadioDatTools.py"
RADIODAT="radioDatFiles/RADIO-usa-d1.DAT"
input_dir='extractedCallBins/usa-d1'

python3 $SCRIPT $RADIODAT Headers -sH

for input in "$input_dir"/*.bin; do
    base_filename=$(basename "$input" .bin)
    output="$input_dir/$base_filename-decrypted"

    python3 $SCRIPT $input $output -xz

done