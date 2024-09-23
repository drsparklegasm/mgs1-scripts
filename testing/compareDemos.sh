#!/bin/bash

# This script runs the python script recursively, first to export all calls, then translate individual calls

input_dir='demoWorkingDir/usa/bins'
output_dir='demoWorkingDir/usa/newBins'

same_count=0
different_count=0

for original in "$input_dir"/*; do
    base_filename=$(basename "$original" .bin) 
    if diff "$original" "$output_dir/$base_filename.bin" >/dev/null; then
        # echo "Files are the same: $original"
        ((same_count++))
    else
        echo "Files are different: $original"
        ((different_count++))
    fi
done

echo "Total files that are the same: $same_count"
echo "Total files that are different: $different_count"
