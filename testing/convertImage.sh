#!/bin/bash

# Directory containing the TGA files
input_dir="graphicsExport"
output_dir="graphicsExport/output"

# Create output directory if it doesn't exist
mkdir -p "$output_dir"

# Loop through all TGA files in the input directory
for input_tga in "$input_dir"/*.tga; do
  # Extract the base filename without extension
  base_filename=$(basename "$input_tga" .tga)
  
  # Set the output PNG and text file paths
  output_png="$output_dir/$base_filename.png"
  output_txt="$output_dir/$base_filename"
  
  # Convert the TGA file to PNG using ImageMagick
  # convert "$input_tga" -resize 300% -colorspace Gray -contrast-stretch 0 "$output_png"
  convert "$input_tga" "$output_png"
  # Perform OCR using Tesseract with Japanese language data and additional options
  # tesseract "$output_png" "$output_dir/$base_filename" -l jpn --psm 6
  # tesseract "$output_png" $output_txt -l jpn --psm 6
  # echo "Printed image $output_txt\n"
done
