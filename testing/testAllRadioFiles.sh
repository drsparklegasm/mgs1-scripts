#!/bin/bash

# This script runs the python script recursively, first to export all calls, then translate individual calls

SPLITSCRIPT="./myScripts/RadioDatTools.py"
RECOMPILESCRIPT="./myScripts/RadioDatRecompiler.py"
input_dir='radioDatFiles'
output_dir='recompiledCallBins'

same_count=0
different_count=0

for input in "$input_dir"/*.DAT; do
    base_filename=$(basename "$input" .DAT)
    echo $base_filename
    python3 $SPLITSCRIPT $input "$output_dir/$base_filename" -xz
done

for original in "$output_dir"/*.xml; do
    base_filename=$(basename "$original" .xml)
    python3 $RECOMPILESCRIPT "$output_dir/$base_filename.xml" "$output_dir/$base_filename-mod.DAT" -x
    if diff "$input_dir/$base_filename.DAT" "$output_dir/$base_filename-mod.DAT" >/dev/null; then
        echo "Files are the same: $original"
        ((same_count++))
    else
        echo "Files are different: $original"
        ((different_count++))
    fi
done

echo "Total files that are the same: $same_count"
echo "Total files that are different: $different_count"

rm recompiledCallBins/*.log