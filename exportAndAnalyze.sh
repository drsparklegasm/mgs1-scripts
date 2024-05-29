#!/bin/bash

# This script runs the python script recursively, first to export all calls, then translate individual calls

SCRIPT="myScripts/RadioDatTools.py"
RADIODAT=$1
input_dir='extractedCallBins'

python3 $SCRIPT $RADIODAT Headers.txt -sH

for input in "$input_dir"/*.bin; do
    base_filename=$(basename "$input" .bin)
    output="$input_dir/$base_filename-decrypted.txt"

    python3 $SCRIPT $input $output 

done