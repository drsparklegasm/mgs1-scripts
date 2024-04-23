# Assumes RADIO.DAT for filename

import os

filename = "RADIO.DAT_USAOrig"

rFile = open(filename, "rb")

print(rFile.read(2))

