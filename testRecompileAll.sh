#!/bin/bash

# This script runs the python script recursively, first to export all calls, then translate individual calls
echo +x

SPLITSCRIPT="./myScripts/RadioDatTools.py"
RECOMPILESCRIPT="./myScripts/RadioDatRecompiler.py"
RADIODAT="radioDatFiles/RADIO-usa-d1.DAT"
input_dir='extractedCallBins'
output_dir='recompiledCallBins'

python3 $SPLITSCRIPT $RADIODAT Headers -sH

for input in "$input_dir"/*.bin; do
    base_filename=$(basename "$input" .bin)
    output="$output_dir/$base_filename"
    python3 $SPLITSCRIPT $input $output -xz
done

for original in "$input_dir"/*.bin; do
    base_filename=$(basename "$original" .bin)
    input="$base_filename-mod.bin"
    echo $base_filename
    python3 $RECOMPILESCRIPT "$output_dir/$base_filename.xml" "$output_dir/$base_filename-mod.bin" -x
    if diff "$original" "$output_dir/$base_filename-mod.bin" >/dev/null; then
        echo "Files are the same: $original"
    else
        echo "Files are different: $original"
    fi
done
