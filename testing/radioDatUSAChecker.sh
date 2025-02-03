#!/bin/bash

# DEPRECATED! Need to update pathing. 
python3 myScripts/RadioDatTools.py radioDatFiles/RADIO-usa-d1.DAT -zx
python3 myScripts/RadioDatRecompiler.py RADIO-usa-d1-output.xml RADIO-usa-d1-recomp.DAT -x
python3 myScripts/incorrectRecompileCheck.py radioDatFiles/RADIO-usa-d1.DAT RADIO-usa-d1-recomp.DAT