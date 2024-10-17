import os, struct
import numpy as np
from PIL import Image


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

creditsFilename = "creditsHacking/00b8b9.rar"
creditsData = open(creditsFilename, 'rb').read()

class imageData:
    width: int
    height: int
    size: tuple [int, int]
    # data
    palette: bytes
    dataLength: int
    compData: bytes
    
    def __init__(self, allData: bytes):
        self.width = struct.unpack('<H', allData[0:2])[0]
        self.height = struct.unpack('<H', allData[2:4])[0]
        self.size = self.width, self.height
        
        self.palette = allData[4:36]
        self.dataLength = struct.unpack('<L', allData[36:40])[0]
        self.compData = allData[40: 40 + self.dataLength]
        
def decompressBytes(gfxData: bytes, size: tuple [int, int]) -> bytes:
    newGfxBytes = b''
    allbytesGenerated = b''
    lines = []
    width, height = size
    length = len(gfxData)
    
    pointer = 0
    while pointer < length:
        command = gfxData[pointer]
        match command:
            case 0x00:
                lines.append(newGfxBytes)
                allbytesGenerated += newGfxBytes
                if len(newGfxBytes) != int(width / 2):
                    print(f'Line did not match! Width: {width}, bytes: {len(newGfxBytes)}. Should be doubled!')
                    # Temporarily finish the line: ???
                    numBytesToAdd = int(width - (len(newGfxBytes) / 2))
                    newGfxBytes += bytes.fromhex('ff') * numBytesToAdd
                newGfxBytes = b''
                pointer += 1
            case 0x40:
                newGfxBytes += bytes.fromhex('ff') * int(width / 2)
                lines.append(newGfxBytes)
                allbytesGenerated += newGfxBytes
                newGfxBytes = b''
                pointer += 1
            case 0x80:
                newGfxBytes += bytes.fromhex('00') * int(width / 2)
                lines.append(newGfxBytes)
                allbytesGenerated += newGfxBytes
                newGfxBytes = b''
                pointer += 1
            case _:
                if command < 0x80:
                    dataToAdd = gfxData[pointer + 1: pointer + 1 + command]
                    newGfxBytes += dataToAdd
                    pointer += command + 1
                elif command > 0x80:
                    numBytesToAdd = command - 0x80
                    position = 0 - gfxData[pointer + 1]
                    if numBytesToAdd > (0 - position):
                        if abs(position) <= len(newGfxBytes):
                            bytesToRepeat = newGfxBytes[position:]
                        else:
                            bytesToRepeat = allbytesGenerated[position:]
                    else:
                        if abs(position) <= len(newGfxBytes):
                            bytesToRepeat = newGfxBytes[position:position + numBytesToAdd]
                        else:
                            bytesToRepeat = allbytesGenerated[position:position + numBytesToAdd]
                    newGfxBytes += bytesToRepeat * int(numBytesToAdd / len(bytesToRepeat))
                    pointer += 2

    print(f'{width} x {height}')
    lines.remove(b'')
    print(f'Height is {height}, we have {len(lines)} lines!')
    
    return lines

def getImages(fileData: bytes) -> list:
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

def outputToTGA():
    print(f'Dostufff')
    
def getColors(palette: bytes) -> list:
    
    # Quick def for getting the RGB values
    def getRGBfromHex(colorBytes: bytes) -> tuple [int, int, int]:
        # Swap the two bytes for little-endian (since color is coming in as a 16-bit integer)
        color = int.from_bytes(colorBytes[i:i+2], byteorder='big')
        color = (color >> 8) | ((color & 0xFF) << 8)

        # Mask out the first bit (16th bit, which is always 0)
        color &= 0x7FFF  # 0x7FFF masks the first bit, leaving 15 bits

        # Extract the 5 bits for Red, Green, and Blue
        r = (color >> 10) & 0x1F  # Red: bits 10-14
        g = (color >> 5) & 0x1F   # Green: bits 5-9
        b = color & 0x1F          # Blue: bits 0-4

        # Normalize the 5-bit values to 8-bit (0-255) range
        r_normalized = int((r / 31) * 255)
        g_normalized = int((g / 31) * 255)
        b_normalized = int((b / 31) * 255)

        # Return normalized 8-bit values for red, green, and blue
        return (r_normalized, g_normalized, b_normalized)
    
    rgbColors = []
    i = 0
    while i < len(palette):
        rgbColors.append(getRGBfromHex(palette[i: i + 2]))
        i += 2
    
    return rgbColors
    
def exportImage(filename: str, image: imageData) -> None:
    # Convert each line of hex into bytes
    pixel_data = decompressBytes(image.compData, (image.width, image.height))

    # Define the image dimensions (you'll need to specify width and height based on your data)
    width = image.width  
    height = image.height
    
    palette = getColors(image.palette)

    # Create an empty image array
    image_array = np.zeros((height, width, 3), dtype=np.uint8)

    # Fill the image array with RGB values from the palette
    for y, line in enumerate(pixel_data):
        for x in range(len(line)):
            byte = line[x]
            low_nibble = (byte >> 4) & 0x0F  # First pixel
            high_nibble = byte & 0x0F  # Second pixel
            
            # Map the nibbles to colors from the palette
            image_array[y, x * 2] = palette[high_nibble]  # First pixel (left)
            image_array[y, x * 2 + 1] = palette[low_nibble]  # Second pixel (right)

    # Create and save the image
    image = Image.fromarray(image_array)
    # image.show()  # This will display the image
    image.save(filename, format="tga")

# def analyzeImage(imgData: bytes) -> tuple[bytes, int, int, bytes]:

if __name__ == "__main__":
    print(f'Outputting graphics from {creditsFilename}')
    imageList: list [imageData] = getImages(creditsData)
    print(f'{len(imageList)} images found!')
    for i, image in enumerate(imageList):
        exportImage(f'file-{i}.tga', image)
        
        
        
    
    