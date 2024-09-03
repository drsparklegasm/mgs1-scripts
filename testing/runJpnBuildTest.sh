#!/bin/bash

# Rebuild japanese iso and launch in duckstation

mkpsxiso build-jpn/rebuild.xml -o mgsJpnMod.bin -c mgsJpnMod.cue -y
flatpak run org.duckstation.DuckStation mgsJpnMod.cue