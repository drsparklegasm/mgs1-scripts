#!/bin/bash

# This script runs the python script recursively, first to export all calls, then translate individual calls

SPLITSCRIPT="myScripts/RadioDatTools.py"
RECOMPILESCRIPT="myScripts/RadioDatRecompiler.py"
RADIODAT="radioDatFiles/RADIO-usa-d1.DAT"
input_dir='extractedCallBins'
output_dir='recompiledCallBins'

rm $input_dir/*
rm $output_dir/*

same_count=0
different_count=0

python3 $SPLITSCRIPT $RADIODAT Headers -s

for input in "$input_dir"/*.bin; do
    base_filename=$(basename "$input" .bin)
    # echo $base_filename
    output="$output_dir/$base_filename"
    python3 $SPLITSCRIPT $input $output -xz
done

for original in "$input_dir"/*.bin; do
    base_filename=$(basename "$original" .bin)
    input="$base_filename-mod.bin"
    python3 $RECOMPILESCRIPT "$output_dir/$base_filename.xml" "$output_dir/$base_filename-mod.bin"
    if diff "$original" "$output_dir/$base_filename-mod.bin" >/dev/null; then
        # echo "Files are the same: $original"
        ((same_count++))
    else
        echo "Files are different: $original"
        ((different_count++))
    fi
done

echo "Total files that are the same: $same_count"
echo "Total files that are different: $different_count"

rm $output_dir/*.log
