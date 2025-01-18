"""
This script re-encodes and tests images originally extracted from the .rar files.

"""
import os, struct
from PIL import Image
import numpy as np
# from creditsHacking.creditsHacking import imageData
import argparse, glob, re

debug = False
blocks = False

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
    global debug
    
    compGfxData = bytes.fromhex('00')
    for line in pixelLines:
        compSegment = compressLine(bytes.fromhex(line))
        if debug:
            print(compSegment.hex(sep=' ', bytes_per_sep=1))   
        compGfxData += compSegment
    
    return compGfxData

# OLDE VERSIONS OF COMPRESSLINE (Deprecated)
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

# New Hotness. This matches in the test data so far.
def compressLineOld2(compressionBytes: bytes) -> bytes:
    """
    Another stab at logically compressing the data. This time the check order is:
    1. Pattern repeated in the earlier data.
    2. Next pattern is a single byte (We either write it and then repeat, or we find it one earlier and repeat it)
    3. Next pattern is a new pattern, we go until there's a character repeated more than 3 times.
    
    ====
    1. check for initial repeated bytes. 
    2. Check if the next few bytes have been seen before.
    3. Find the next unique pattern, including the next repeated byte.

    """

    def findLongerFit(data: bytes, index: int) -> bool:
        """
        This function will check repeating one character is longer than a repeated pattern
        """
        before = data[:index]
        after = data[index:]

        count = 1
        matchByte = after[0].to_bytes()
        for i in range(0, len(after)):
            if after[i].to_bytes() == matchByte:
                count += 1
            else:
                break

        patternCount = 1
        for i in range(0, len(after)):
            if before.find(after[:patternCount]) != -1:
                patternCount += 1
            else:
                break
        
        if count > patternCount:
            return True
        else:
            return False

    index = 0
    compressedData = b''

    while index < len(compressionBytes):
        writtenBytes = compressionBytes[:index]
        workingBytes = compressionBytes[index:]
        count = 1
        
        # First check for single repeated byte:
        if (workingBytes[0].to_bytes() * 3) == workingBytes[0:3] and writtenBytes.find(workingBytes[0:5]) != -1:
            # FIrst byte repeats at least 4 times. Find how many total:
            matchByte = workingBytes[0].to_bytes()
            while count < min(128, len(workingBytes)):
                if workingBytes[count].to_bytes() == matchByte: # should rewrite as gpt suggested... if len(set(workingBytes[:count])) == 1:
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
                    # Find the soonest that 3 bytes at least are repeated.
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

def compressLine(data: bytes) -> bytes:

    global debug

    def findNextPatternOrRepeat(data: bytes, index: int) -> int:
        """
        Finds how many bytes starting at index
        until either we repeat the same byte 4x 
        or the next 4 bytes are a repeated pattern
        """
        count = 0
        checkLength = 3
        while True:
            patternCheck = data[index + count: index + count + checkLength]
            if len(set(patternCheck)) == 1 or data[:index + count].find(patternCheck) != -1:
                break
            else:
                count += 1
        
        return count

    def getLongestRepeat(data: bytes, index: int) -> int:
        """
        Get the longest repeated character starting at index.
        """

        before = data[:index]
        after = data[index:]

        count = 0
        while count < min(128, len(after)):
            if len(set(after[:count + 1])) == 1:
                count += 1
            else:
                break

        # print(f'{count} bytes were repeated following index {index}' )
        return count

    def getLongestPattern(data: bytes, index: int) -> tuple [int, int]:
        """
        For the index, return the longest pattern starting there that 
        appears earlier in the data and how far back to go.
        """
        before = data[:index]
        after = data[index:]

        count = 0
        while count < len(after):
            if before.find(after[:count + 1]) != -1:
                count += 1
            else:
                break
        
        distance = abs(len(before) - before.rfind(after[:count]))

        return distance, count
    
    """
    Actual compression Def starts here.

    """
    
    compressedData = b''
    i = 0

    while i < len(data):
        newBytes = b''
        repeatCount = getLongestRepeat(data, i)
        distance, patternLen = getLongestPattern(data, i)

        if patternLen >= repeatCount and patternLen > 1:
            if data[i - 1] == data[i]:
                newBytes += (repeatCount + 0x80).to_bytes() + int(1).to_bytes()
                i += repeatCount
            else:
                newBytes += (patternLen + 0x80).to_bytes() + distance.to_bytes()
                i += patternLen
        elif repeatCount > 3:
            if data[i - 1] == data[i] and i != 0:
                newBytes += (repeatCount + 0x80).to_bytes() + int(1).to_bytes()
                i += repeatCount
            else:
                newBytes += int(1).to_bytes() + data[i].to_bytes()
                newBytes += (repeatCount - 1 + 0x80).to_bytes() + int(1).to_bytes()
                i += repeatCount
        else:
            newString = findNextPatternOrRepeat(data, i)
            if newString < 1:
                newString = 1
            newBytes += newString.to_bytes() + data[i : i + newString]
            i += newString
        
        compressedData += newBytes
    
    compressedData += bytes.fromhex('00')
    
    """if debug: 
        print(f'Compressed data: {compressedData.hex(sep=' ')}')"""
    
    return compressedData

def formatImage(filename: str) -> bytes:
    global blocks
    # Assume you have a PIL Image object
    image = Image.open(filename) 

    # Convert PIL Image to NumPy array
    image_array = np.array(image)

    # Get the palette from the image
    imagePalette = getPalette(image_array)

    # Convert the palette to bytes
    paletteBytes = paletteToBytes(imagePalette)
    outputLines = writeLines(image_array, imagePalette)
    
    if blocks:
        # Write the lines to a text file
        newFilename = filename.split('/')[-1].split('.')[0]
        with open(f'creditsHacking/output/verification/{newFilename}-blocks.txt', 'w') as f:
            for line in outputLines:
                f.write(f'{line}\n')
    
    # Output the file in original MGS Compressed format
    outputImageData = b''

    # Width, height
    height = struct.pack('H', len(outputLines))
    width = struct.pack('H', len(outputLines[0]))
    outputImageData += width + height

    # Palette
    outputImageData += paletteBytes

    # Compress the image data
    compressedData = compressImageData(outputLines)
    dataLength = len(compressedData)
    outputImageData += struct.pack('I', dataLength)

    # Final check before adding image data3
    # print(f'Header: {outputImageData.hex(sep=' ', bytes_per_sep=1)}')

    # Add the compressed data
    outputImageData += compressedData

    return outputImageData

## MAIN BRANCH

def numerical_sort(value):
    """
    Needed for the files to be sorted by number correctly
    """
    parts = re.split(r'(\d+)', value)
    return [int(part) if part.isdigit() else part for part in parts]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a TGA file to a text file')
    parser.add_argument('--filename', '-f', nargs="?", type=str, help='The filename of the TGA file to convert')
    parser.add_argument('--folder', '-d', type=str, help='Directory of files to grab')
    parser.add_argument('--output', '-o', nargs="?", type=str, help='The filename of the output archive filename.')
    parser.add_argument('--blocks', '-b', action='store_true', help='outputs the blocks for reviewing pixel data.')
    args = parser.parse_args()

    # File buffer, ensures each image aligns with a multiple of this
    bufferNum = 4

    """print(f'Filename: {args.filename}')"""
    print(f'Folder: {args.folder}')
    
    if args.filename is not None:
        fileList = [args.filename]
    else:
        fileList = glob.glob(f'{args.folder}/*.tga')
        fileList.sort(key=numerical_sort)
    
    blocks = args.blocks
    
    fileData = struct.pack('I', len(fileList)) # Should be the number of files we're importing either way.
    
    for file in fileList:
        print(f'Processing {file}...')
        addBytes = formatImage(file)
        # Buffer the number of bytes
        addBytes += bytes(0) * (len(addBytes) % bufferNum)
        fileData += addBytes

    with open('creditsHacking/output/recompressedImage.bin', 'wb') as f:
        f.write(fileData)
    f.close()


## TESTING BRANCH 
"""malfunctioningLine = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6f11f52e13fb04ffffffbf70ffff1505fb6fb0ffffffff08f7ffeb9fa0ffffff0806f6cf70ff06fbffef40ffdeff22fe8f805fc0ffff09f905fd7f70ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
if __name__ == "__main__":
    # This is just a minimal test.
    print(compressLine(bytes.fromhex(malfunctioningLine)).hex(sep=' ', bytes_per_sep=1))
    """