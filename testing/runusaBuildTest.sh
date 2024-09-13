#!/bin/bash

# Rebuild USA iso and launch in duckstation

mkpsxiso build/rebuild.xml -o mgsUSAMod.bin -c mgsUSAMod.cue -y
flatpak run org.duckstation.DuckStation mgsUSAMod.cue