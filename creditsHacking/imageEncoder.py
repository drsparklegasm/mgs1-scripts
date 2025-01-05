"""
This script re-encodes and tests images originally extracted from the .rar files.

"""
import os
from PIL import Image
import numpy as np
# from creditsHacking.creditsHacking import imageData
import argparse

imagePalette = []

def getPalette(numpyArray: np.array) -> list:
    """
    This will iterate through the numpy arrary and return a list of unique colors.
    We return a palette list object with rgb tuples.
    """
    palette = [] # Instantiate the specific array type

    """ # This is my way, but there's a better one suggested by copilot.
    for y, line in enumerate(image_array):
        for x in range(len(line) // 2):
            # Get the RGB values for the two pixels
            pixel1 = tuple(int(value) for value in line[x * 2])
            pixel2 = tuple(int(value) for value in line[x * 2 + 1])

            # Print the RGB values
            # print(f'Pixel 1: {pixel1}, Pixel 2: {pixel2}')
            if pixel1 not in palette:
                palette.append(pixel1)
            if pixel2 not in palette:
                palette.append(pixel2)
                """
    
    # Get all unique pixel tuples
    unique_pixels = np.unique(image_array.reshape(-1, image_array.shape[2]), axis=0)

    # Convert the unique pixels to a list of tuples
    unique_pixel_tuples = [tuple(pixel) for pixel in unique_pixels]
    for pixel in unique_pixel_tuples:
        palette.append(tuple(int(value) for value in pixel))

    return palette

def paletteToBytes(colors: list[tuple[int, int, int]]) -> bytes:
    """
    This will convert a list of RGB colors to a bytes object.
    Bytes returned will be no more than 16 colors, 32 bytes (0x20)
    """

    # Color limit check
    if len(colors) > 16:
        raise ValueError('Palette has more than 16 colors! Original game uses no more than 16 distinct colors.')
    
    colorBytes = b''
    # r, g, b = 0, 0, 0

    for color in colors:
        r, g, b = color
        r = int((r * 32) / 255)
        g = int((g * 32) / 255)
        b = int((b * 32) / 255)

        # Combine the 5-bit values into a single 16-bit value
        colorValue = (r << 10) | (g << 5) | b
        # print(f'{color}, {colorValue:04x}')
        # Reverse the byte order
        colorBytes = colorValue.to_bytes(2, byteorder='little') + colorBytes

    return colorBytes

def writeLines(numpyArray: np.array, palette: list[tuple [int, int, int]]) -> list[str]:
    """
    creates the lines needed for the image.
    """
    pixelLines = []

    for y, line in enumerate(image_array):
        pixelLine = ''
        for x in range(len(line) // 2):
            # This is ugly but if i don't do it we get numpy specific objects in the tuple
            indexB = 15 - palette.index(tuple(int(value) for value in line[x * 2]))
            indexA = 15 - palette.index(tuple(int(value) for value in line[x * 2 + 1]))

            byte = (indexA << 4) | indexB
            pixelLine += f'{byte:02x}'
        pixelLines.append(pixelLine)

    return pixelLines

"""
# Get the palette from the image
imagePalette = getPalette(image_array)
# Convert the palette to bytes
paletteBytes = paletteToBytes(imagePalette)

# Print the palette bytes
print(len(paletteBytes))
print(paletteBytes.hex(sep=' ', bytes_per_sep=1))

outputLines = writeLines(image_array, imagePalette)

with open('output.txt', 'w') as f:
    for line in outputLines:
        f.write(f'{line}\n')
        
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a TGA file to a text file')
    parser.add_argument('filename', type=str, help='The filename of the TGA file to convert')
    args = parser.parse_args()

    # Assume you have a PIL Image object
    image = Image.open(args.filename) 

    # Convert PIL Image to NumPy array
    image_array = np.array(image)

    # Get the palette from the image
    imagePalette = getPalette(image_array)
    # Convert the palette to bytes
    paletteBytes = paletteToBytes(imagePalette)

    

    outputLines = writeLines(image_array, imagePalette)

    newFilename = args.filename.split('/')[-1].split('.')[0]
    with open(f'creditsHacking/output/verification/{newFilename}-blocks.txt', 'w') as f:
        for line in outputLines:
            f.write(f'{line}\n')
    
    # Print the palette bytes
    print(f'{newFilename.split('-')[-1]}: {paletteBytes.hex()}')