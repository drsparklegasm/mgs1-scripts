#!/bin/bash

# Rebuild japanese iso and launch in duckstation



# 

mkpsxiso build/jpn-d1/rebuild.xml -o mgsJpnMod-d1.bin -c mgsJpnMod-d1.cue -y
mkpsxiso build/jpn-d2/rebuild.xml -o mgsJpnMod-d2.bin -c mgsJpnMod-d2.cue -y
flatpak run org.duckstation.DuckStation mgsJpnMod-d1.cue

