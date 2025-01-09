"""
This script re-encodes and tests images originally extracted from the .rar files.

"""
import os
from PIL import Image
import numpy as np
# from creditsHacking.creditsHacking import imageData
import argparse

# testData from first image:

testDataA = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
# Bytes should be 01 FF / FF 01 / A0 01 / 00
# My bytes: 02 ff ff 82 9e 00
testDataB = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffeeeeeefeffefeeffffefeeeeeeeeeeeeeefeffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
testDataC = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff2e80eeaeeb06434411bea3ee4ea0ff0ee0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'


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

    for y, line in enumerate(numpyArray):
        pixelLine = ''
        for x in range(len(line) // 2):
            # This is ugly but if i don't do it we get numpy specific objects in the tuple
            indexB = 15 - palette.index(tuple(int(value) for value in line[x * 2]))
            indexA = 15 - palette.index(tuple(int(value) for value in line[x * 2 + 1]))

            byte = (indexA << 4) | indexB
            pixelLine += f'{byte:02x}'
        pixelLines.append(pixelLine)

    return pixelLines

def getBestPattern(data: bytes) -> tuple[bytes, int, int]:
    """
    This will return the best pattern found in the data.
    TUPLE HAS: (pattern, count, total length)
    """
    patterns = []
    bestPattern = (b'', 0, 0)
    dataLength = len(data)
    patternLength = 1
    pointer = 0
    count = 1
    
    # First loop is for how long to make the pattern
    while patternLength < (dataLength // 2): # If it were half length we could only repeat it twice.
        # Initialize the pattern and pointer
        pattern = data[0:patternLength]
        pointer = patternLength
        
        # Second loop is for how many times the pattern repeats
        while pointer <= dataLength and count < 128: # Can't exceed 0x80 times...
            # Check if the pattern repeats
            if data[pointer: pointer + patternLength] == pattern:
                count += 1
                pointer += patternLength
                # Check if we've reached the end of the data
                if pointer == dataLength:
                    if bestPattern[2] < patternLength * count:
                        bestPattern = (pattern, count, patternLength * count)
                    patterns.append((patternLength, count, patternLength * count))
                    break
            else: # Pattern doesn't repeat, end the check here
                if bestPattern[2] < patternLength * count: # check if this pattern is better than the current best pattern
                    bestPattern = (pattern, count, patternLength * count)
                patterns.append((pattern, count, patternLength * count))
                break
        # Reset counters for next pattern check
        patternLength += 1
        count = 1
        
    # Remember to account ELSEWHERE for extra bytes that continue a part of the pattern!
    """for p in patterns:
        print(p)"""
    return bestPattern

def compressImageData(pixelLines: list [str]) -> bytes:
    """
    This will compress the image data into bytes as it would be in the original game.
    We'll need the image data, the palette, and the width of the image.
    """
    
    compGfxData = b''
    for line in pixelLines:
        compSegment = compressLine(line)
        compGfxData += compSegment
    
    return compGfxData

def compressLine(data: str) -> bytes:
    """
    Compress a single line of pixel data.
    
    I think we can test how much we can compress 3 possibilities:
    0. If the remaining bytes are all 00's add a 0x80 and ends the line.
    1. Check if a single byte is repeated, and if so how many times.
    2. Check if a pattern is repeated, and if so how many times.
    3. check if the next pattern was already seen, and if so how long ago
    4. (last resort) we have a new pattern.
    
    First approach is to use the byte search for repeated patterns. We'll iterate until we reach a length of pattern not repeated.
    """
    compressedData = b''
    pointer = 0
    dataLength = len(data) // 2
    
    """
    Boolean tests:
    1. Is it one byte?
    2. Is it a repeated byte or pattern?
    3. Has it been seen before?

    We should test first if it's been seen before.
    Then if it's one or many bytes.
    
    """
    
    databytes = bytes.fromhex(data)
    while pointer < dataLength:
        # Get the best next pattern to add. Then add based on logic we can find. 
        nextPattern = getBestPattern(databytes[pointer:])
        # TUPLE HAS: (pattern, count, total length)!! 

        if len(nextPattern[0]) == 1:
            # Add logic for single byte repeated
            compressedData += bytes.fromhex('01')
            compressedData += nextPattern[0]
            repeatNum = nextPattern[1] - 1 # We already added the first byte, now how many times do we repeat it?
            # Calculate the next byte is 0x80 more to denote a repeat. 
            nextByte = (repeatNum + 0x80).to_bytes()
            compressedData += nextByte
            compressedData += bytes.fromhex('01') # Pattern to repeat is pointed one prior
            # Add the total length added to the pointer for next go-round
            pointer += nextPattern[2]
        elif databytes[pointer - len(nextPattern[0]) : pointer] == nextPattern[0]: # pattern appears in prior data
            nextByte = (len(nextPattern[0]) + 0x80).to_bytes()
            compressedData += nextByte
            compressedData += nextPattern[2].to_bytes() # Pattern to repeat is pointed one prior
            # Add the total length added to the pointer for next go-round
            pointer += nextPattern[2]# Repeat some of the logic of repeating the single byte X times
        elif nextPattern[1] == 1 and databytes.find(nextPattern[0]) != -1: # new pattern, repeated
            index = abs(databytes.find(nextPattern[0]) - pointer)
            # Find the latest occurrence of the patern, if there are multiple
            while index > 128 and databytes.find(nextPattern[0]) != -1: 
                index = abs(databytes.find(nextPattern[0]) - pointer)
            # Add the bytes in
            nextByte = (index + 0x80).to_bytes()
            compressedData += nextByte
            compressedData += nextPattern[2].to_bytes()
            pointer += nextPattern[2]
        else: # Assuming new pattern, and it's not found previously, written once.
            compressedData += len(nextPattern[0]).to_bytes()
            compressedData += nextPattern[0]
            pointer += len(nextPattern[0])
    
    compressedData += bytes.fromhex('00') # End of line

    return compressedData

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

## TESTING BRANCH 
if __name__ == "__main__":
    bestPattern = getBestPattern(bytes.fromhex(testDataA))
    print(bestPattern)

    lines = [testDataB]
    compressedData = compressImageData(lines)
    print(compressedData.hex())

## MAIN BRANCH
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
    print(f'{newFilename.split('-')[-1]}: {paletteBytes.hex()}')"""