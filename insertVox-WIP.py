"""
This rough script inserts a different VAG audio file into a VOX file. 
"""

# import demoManager as DM
from demoClasses import *

voxFilename = ""
vagFilename = ""

VAG_HEADER_LENGTH = 0x40

originalDemo = demo(0, open(voxFilename, 'rb').read())

# Create the vag header:

