#!/bin/bash

# This script runs the python script recursively, first to export all calls, then translate individual calls

SPLITSCRIPT="myScripts/RadioDatTools.py"
RECOMPILESCRIPT="myScripts/RadioDatRecompiler.py"
RADIODAT="radioDatFiles/$1"
input_dir="extractedCallBins/$2"
# output_dir="recompiledCallBins/$2"

rm $input_dir/*
# rm $output_dir/*

same_count=0
different_count=0

python3 $SPLITSCRIPT $RADIODAT Headers -s

for input in "$input_dir"/*.bin; do
    base_filename=$(basename "$input" .bin)
    # echo $base_filename
    output="$input_dir/$base_filename"
    python3 $SPLITSCRIPT $input $output -xz
done

echo "Total files that are the same: $same_count"
echo "Total files that are different: $different_count"

# rm $output_dir/*.log
