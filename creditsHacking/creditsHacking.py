import os, struct
import numpy as np
from PIL import Image
import argparse


"""
Notes from Green Goblin:

# Header
- First 4 bytes: Little endian number of files
- 2 bytes width, LE
- 2 bytes height, LE
- following 32 bytes (0x20) are the color palette (16 colors, 2 bytes each)
- 4 bytes compressed image size, LE (NOT part of the image)

# Compressed bytes:

0x00 == End of a line
0x40 == a full line with the last color of the palette

"""

# Been testing a bunch of these
creditsFilename = "creditsHacking/usa/00b8ba.rar"
creditsFilename = "creditsHacking/usa/00b8b9.rar"
creditsFilename = "creditsHacking/usa/00eae8.rar"
# creditsFilename = "creditsHacking/goblinExample/spanishBinFile.bin"
# creditsFilename = "creditsHacking/jpn/00eae8.rar"

filesToRun = [
    "creditsHacking/00eae8.rar",
    "creditsHacking/goblinExample/spanishBinFile.bin",
    "creditsHacking/jpn/00eae8.rar"
]

spanish = False
creditsData = open(creditsFilename, 'rb').read()

class imageData:
    width: int
    height: int
    size: tuple [int, int]
    # data
    palette: bytes
    dataLength: int
    compData: bytes
    lines = []
    
    def __init__(self, allData: bytes):
        self.width = struct.unpack('<H', allData[0:2])[0]
        self.height = struct.unpack('<H', allData[2:4])[0]
        self.size = self.width, self.height
        
        self.palette = allData[4:36]
        self.dataLength = struct.unpack('<L', allData[36:40])[0]
        self.compData = allData[40: 40 + self.dataLength]
        
# def decompressBytes(gfxData: bytes, size: tuple [int, int]) -> bytes:
def decompressBytes(image: imageData) -> bytes:
    """
    This is the main logic to decompress the image data. 
    Based on GreenGoblin's hacked logic. 
    """
    global spanish
    gfxData: bytes = image.compData
    width, height = image.width, image.height
    newGfxBytes = b''
    allbytesGenerated = b''
    lines = []
    length = len(gfxData)

    log = open('creditsHacking/output/extactImageLog.txt', 'w')
    
    pointer = 0
    while pointer < length:
        # Before we evaluate, check if we're over length. If so, add the line and reset.
        if len(newGfxBytes) > int(width / 2):
            lines.append(newGfxBytes[0:int(width / 2)])
            allbytesGenerated += newGfxBytes
            newGfxBytes = b''
            # This is to be used in conjunction with the other logic for > 0x80"""

        command = gfxData[pointer]
            
        if command == 0x00:
            # End of a line
            lines.append(newGfxBytes)
            allbytesGenerated += newGfxBytes
            newGfxBytes = newGfxBytes[int(width / 2):]
            pointer += 1

            log.write(f'Command: {command.to_bytes().hex()} - ENDING LINE \n')
                
        elif command == 0x80 or (spanish and command == 0x40):
            # New logic (before removal)
            if command == 0x80:
                fillByte = bytes.fromhex('00')
            else:
                fillByte = bytes.fromhex('FF')

            # Find remaining bytes and fill with color
            remainLine = int(width / 2) - len(newGfxBytes)
            newGfxBytes += fillByte * remainLine
            
            # Add to the lines
            lines.append(newGfxBytes)
            allbytesGenerated += newGfxBytes 
            
            # In case this was hit mid-line, fill the rest on the next line
            newGfxBytes = fillByte * (int(width / 2 ) - remainLine)
            pointer += 1

            log.write(f'Command: {command.to_bytes().hex()} - Wrote {fillByte.hex()} to end of line. Wrote {remainLine} new bytes in new line. \n')

        elif command < 0x80:
            # The simple one
            dataToAdd = gfxData[pointer + 1: pointer + 1 + command]
            newGfxBytes += dataToAdd
            pointer += command + 1

            log.write(f'Command: {command.to_bytes().hex()} - Adding {int(command)} bytes: "{dataToAdd.hex()}" \n')

        else: # command > 0x80:
            # Find number of bytes to add
            numBytesToAdd = command - 0x80
            # How far back do we go to find the byte(s) we're adding
            position = 0 - gfxData[pointer + 1]
            # bytesToRepeat = newGfxBytes[position:]
            if numBytesToAdd > abs(position):
                bytesToRepeat = newGfxBytes[position:]
                # If we just sent back a line, grab from last bytes done
                if len(newGfxBytes) == 0: 
                    bytesToRepeat = allbytesGenerated[position:]
                addbytes = bytesToRepeat * int(numBytesToAdd / len(bytesToRepeat))
                newGfxBytes += addbytes
                # Checking for uneven repeats, we repeat until the numBytes is satisfied
                if numBytesToAdd % abs(position) > 0:
                    # print(f'Line: {len(lines)} Adding {numBytesToAdd}, but only {abs(position)} to work with!')
                    addbytes = bytesToRepeat[0 : numBytesToAdd % abs(position) ]
                    newGfxBytes += addbytes
            else:
                # Distinguish position to end of line from being a number less than that number's absolute
                if position + numBytesToAdd == 0:
                    addbytes = newGfxBytes[position: ]
                else:
                    addbytes = newGfxBytes[position: position + numBytesToAdd]
                newGfxBytes += addbytes 
            pointer += 2

            log.write(f'Command: {command.to_bytes().hex()} Position: {position} - > 0x80: Repeating: Added {numBytesToAdd} bytes. Wrote {addbytes.hex()} \n')

    # Cleanup, as there are some extra 0x00's 
    if b'' in lines:
        lines.remove(b'')
    
    log.close()
    
    # print(f'Height is {height}, we have {len(lines)} lines!') # Debug no longer needed
    image.lines = lines # This currently won't happen because the image is not returned!
    return lines


def getImages(fileData: bytes) -> list:
    """
    Gets the images from a file. Returns list of imageData objects
    """
    images = []
    numImg = struct.unpack('<L', fileData[0:4])[0]
    i = 0
    nextImage = 4
    while i < numImg:
        a = imageData(fileData[nextImage:])
        images.append(a)
        nextImage += images[-1].dataLength + 40
        i += 1
    
    return images
    
def getColors(palette: bytes) -> list:
    """
    Returns a list of colors in the palette.
    Each color is a Tuple (r, g, b) of 0 <= 255
    """
    # Quick def for getting the RGB values
    def getRGBfromHex(colorBytes: bytes) -> tuple [int, int, int]:
        """
        Calculates the color from the 2-byte color in the palette.
        """
        # Swap the two bytes for little-endian (since color is coming in as a 16-bit integer)
        color = int.from_bytes(colorBytes, byteorder='big')
        color = (color >> 8) | ((color & 0xFF) << 8)

        # Mask out the first bit (16th bit, which is always 0)
        color &= 0x7FFF  # 0x7FFF masks the first bit, leaving 15 bits

        # Extract the 5 bits for Red, Green, and Blue
        r = (color >> 10) & 0x1F  # Red: bits 10-14
        g = (color >> 5) & 0x1F   # Green: bits 5-9
        b = color & 0x1F          # Blue: bits 0-4

        # Normalize the 5-bit values to 8-bit (0-255) range 
        # Special note. Math gets funky here, so leave it at 31 or it won't recompile correctly!
        r_normalized = int((r / 31) * 255)
        g_normalized = int((g / 31) * 255)
        b_normalized = int((b / 31) * 255)

        # Return normalized 8-bit values for red, green, and blue
        return (r_normalized, g_normalized, b_normalized)
    
    rgbColors = []
    i = 0
    # Loop through the palette, getting the RGB values for each color [2 bytes each]
    while i < len(palette):
        nextColor = getRGBfromHex(palette[i: i + 2])
        rgbColors.append(nextColor)
        i += 2
    
    return rgbColors
    
def exportImage(filename: str, image: imageData) -> None:
    # Convert each line of hex into bytes
    palette = getColors(image.palette)
    # pixel_data = decompressBytes(image.compData, (image.width, image.height))
    pixel_data = decompressBytes(image)

    # Define the image dimensions (you'll need to specify width and height based on your data)
    width = image.width  
    height = image.height

    # Create an empty image array
    image_array = np.zeros((height, width, 3), dtype=np.uint8)

    # Fill the image array with RGB values from the palette
    for y, line in enumerate(pixel_data):
        for x in range(len(line)):
            byte = line[x]
            # Swap the nibbles; the first nibble (left) is the high-order bits, the second nibble is the low-order bits
            low_nibble = (byte >> 4) & 0x0F  # First pixel
            high_nibble = byte & 0x0F  # Second pixel
            
            # Map the nibbles to colors from the palette
            image_array[y, x * 2] = palette[high_nibble]  # First pixel (left)
            image_array[y, x * 2 + 1] = palette[low_nibble]  # Second pixel (right)

    # Create and save the image
    image = Image.fromarray(image_array)
    # image.show()  # This will display the image
    image.save(f'{filename}')

    return

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description='Extracts images from the credits file.')
    argparser.add_argument('filename', type=str, help='The filename of the credits file to extract images from.')
    args = argparser.parse_args()

    creditsFilename = args.filename

    print(f'Outputting graphics from {creditsFilename}')
    creditsData = open(creditsFilename, 'rb').read()

    # Make a list of imageData objects, list how many were found.
    imageList: list [imageData] = getImages(creditsData)
    print(f'{len(imageList)} images found!')
    
    paletteCheck = open('creditsHacking/output/paletteCheck.txt', 'w')
    # For each image found, output an image file.
    for i, image in enumerate(imageList):
        # 1. Export the file
        exportImage(f'creditsHacking/output/images/file-{i}.tga', image)
        # 2. Export the blocks (lines of hex chars), this is mostly for verification later.
        with open(f'creditsHacking/output/blocks/file-{i}-blocks.txt', 'w') as f:
            for line in image.lines:
                f.write(f'{line.hex()}\n')
        paletteCheck.write(f'{i}: {image.palette.hex()}\n')
        print(f'Palette for image {i}: {image.palette.hex()}')
        print(f'IMAGE {i} DONE!\n')

    paletteCheck.close()
    