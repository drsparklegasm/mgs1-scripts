#!/bin/bash

# Rebuild japanese iso and launch in duckstation

mkpsxiso build/usa-d1/rebuild.xml -o mgsUSAMod-d1.bin -c mgsUSAMod-d1.cue -y
mkpsxiso build/usa-d2/rebuild.xml -o mgsUSAMod-d2.bin -c mgsUSAMod-d2.cue -y
flatpak run org.duckstation.DuckStation mgsUSAMod-d1.cue