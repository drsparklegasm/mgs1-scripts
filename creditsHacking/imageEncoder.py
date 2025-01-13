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
testDataB = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f21fe9f11fb14000059000110fe3e60ff8fb2ffffffffcf0300d49f010040ff5f40ffcf0100b3ffffff3c0092ff6f0030fb6fd2ffff19f9150051fdffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
"""
Command: 01 - Adding 1 bytes: "ff" 
Command: b1 Position: -1 - > 0x80: Repeating: Added 49 bytes. Wrote ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 
Command: 13 - Adding 19 bytes: "7f21fe9f11fb14000059000110fe3e60ff8fb2" 
Command: 84 Position: -23 - > 0x80: Repeating: Added 4 bytes. Wrote ffffffff 
Command: 10 - Adding 16 bytes: "cf0300d49f010040ff5f40ffcf0100b3" 
Command: 83 Position: -19 - > 0x80: Repeating: Added 3 bytes. Wrote ffffff 
Command: 12 - Adding 18 bytes: "3c0092ff6f0030fb6fd2ffff19f9150051fd" 
Command: b2 Position: -110 - > 0x80: Repeating: Added 50 bytes. Wrote ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 
Command: 00 - ENDING LINE 
"""
## 01 FF B1 01 13 7F 21 FE 9F 11 FB 14 00 00 59 00 01 10 FE 3E 60 FF 8F B2 84 17 10 CF 03 00 D4 9F 01 00 40 FF 5F 40 FF CF 01 00 B3 83 13 12 3C 00 92 FF 6F 00 30 FB 6F D2 FF FF 19 F9 15 00 51 FD B2 6E 00
testDataC = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6f00f95f00fb049999bd6940a9ff0a21ff6fb0ffffffff2e708b709f509ab9ff1d01fccf408a12fdffff23ba33ff07b419e25fc0ffff09f9057604e3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
# 01 FF B1 01 13 6F 00 F9 5F 00 FB 04 99 99 BD 69 40 A9 FF 0A 21 FF 6F B0 84 17 25 2E 70 8B 70 9F 50 9A B9 FF 1D 01 FC CF 40 8A 12 FD FF FF 23 BA 33 FF 07 B4 19 E2 5F C0 FF FF 09 F9 05 76 04 E3 B2 6E 00 
# 


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
    unique_pixels = np.unique(numpyArray.reshape(-1, numpyArray.shape[2]), axis=0)

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

# OLDE VERSION OF COMPRESSLINE
"""
This is my first version, it does alright but it does not match the original compressed data.
"""
def compressLineOld(data: str) -> bytes:
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
    Another stab at logically compressing the data. This time the check order is:
    1. Pattern repeated in the earlier data.
    2. Next pattern is a single byte (We either write it and then repeat, or we find it one earlier and repeat it)
    3. Next pattern is a new pattern, we go until there's a character repeated more than 3 times.
    """

# New Hotness. This matches in the test data so far.
def compressLine(compressionBytes: bytes) -> bytes:
    """
    1. check for initial repeated bytes. 
    2. Check if the next few bytes have been seen before.
    3. Find the next unique pattern, including the next repeated byte.

    """
    index = 0
    compressedData = b''

    while index < len(compressionBytes):
        writtenBytes = compressionBytes[:index]
        workingBytes = compressionBytes[index:]
        count = 1
        
        # First check for single repeated byte:
        if (workingBytes[0].to_bytes() * 3) == workingBytes[0:3]:
            # FIrst byte repeats at least 4 times. Find how many total:
            matchByte = workingBytes[0].to_bytes()
            while count < min(128, len(workingBytes)):
                if workingBytes[count].to_bytes() == matchByte:
                    count += 1
                else:
                    break
            # Write it either as new data (4 bytes compressed) or as a repeat (2 bytes compressed)
            if writtenBytes.find(matchByte) != -1:
                # Byte is found in the written bytes. 
                """
                As an aside, this is super dumb. If the last byte is the same as the matchByte, we need to write it as a repeat. 
                But if it's not, we look for a long length of the repeated byte earlier in the data.
                Seems inconsequential to differentiate, but it's necessary to match the original data.
                """
                if writtenBytes[-1:] == matchByte:
                    # If the byte is the last byte of the compressed data... 
                    lastOcc = writtenBytes.rfind(matchByte)
                else:
                    # If the byte is NOT the last byte of the compressed data...
                    lastOcc = writtenBytes.rfind(matchByte * count)
                seekNum = len(writtenBytes) - lastOcc
                compressedData += (count + 0x80).to_bytes()
                compressedData += seekNum.to_bytes()
            else:
                # Byte is not found in the written bytes. Write it once.
                compressedData += int(1).to_bytes() + matchByte
                compressedData += (count - 1 + 0x80).to_bytes() + int(1).to_bytes() 
        else:
            # find the longest repeated pattern that can be made:
            while count < 128:
                if writtenBytes.find(workingBytes[:count + 1]) != -1:
                    count += 1
                else:
                    break # Breaks when the pattern is no longer repeated.
            if count > 3:
                # We have a repeated pattern. Find the last occurrence of it.
                lastOcc = writtenBytes.rfind(workingBytes[:count])
                seekNum = len(writtenBytes) - lastOcc
                compressedData += (count + 0x80).to_bytes()
                compressedData += seekNum.to_bytes()
            else:
                # new pattern, stop when something else is repeated 3 bytes or more.
                limit = min(128, len(workingBytes) - 1)
                while count < limit:
                    print(f'{(workingBytes[count].to_bytes() * 3).hex()} - {workingBytes[count: count + 3].hex()}')
                    if (workingBytes[count].to_bytes() * 3) == workingBytes[count: count + 3]:
                        break
                    else:
                        count += 1
                compressedData += count.to_bytes()
                compressedData += workingBytes[:count]
        # Either case count is added to the index pointer.
        print(f'{compressedData.hex(sep=" ", bytes_per_sep=1)}')    
        index += count
    
    # Add the end of line byte
    compressedData += int(0).to_bytes()
    # Line encoded, return the compressed bytes.
    return compressedData

    """pointer = 1
    compressedData = b''
    
    while pointer < len(line):
        previous = line[:pointer]
        nextPattern = newGetBestPattern(line[pointer:])"""


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
    # This is just a minimal test.
    print(compressLine(bytes.fromhex(testDataC)).hex(sep=' ', bytes_per_sep=1))

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

    
    # Write the lines to a text file
    newFilename = args.filename.split('/')[-1].split('.')[0]
    with open(f'creditsHacking/output/verification/{newFilename}-blocks.txt', 'w') as f:
        for line in outputLines:
            f.write(f'{line}\n')
    
    # Print the palette bytes
    print(f'{newFilename.split('-')[-1]}: {paletteBytes.hex()}')"""