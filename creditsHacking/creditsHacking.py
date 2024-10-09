import os, struct

"""
Notes from Green Goblin:

# Header
- First 4 bytes: Little endian number of files
- 2 bytes width, LE
- 2 bytes height, LE
- following 32 bytes  (0x20) are the color palette
- 4 bytes compressed image size, LE (NOT part of the image)

# Compressed bytes:

0x00 == End of a line
0x40 == a full line with the last color of the palette



"""

creditsFilename = ""
creditsData = open(creditsFilename, 'rb').read()



def extractGraphic():

    return

def processLine():
    """
    A line ends on \x00
    """
    return
