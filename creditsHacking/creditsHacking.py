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



def decompressBytes(gfxData: bytes, size: tuple [int, int]) -> bytes:
    newGfxBytes = b''
    lines = []
    width, height = size
    length = len(gfxData)

    pointer = 0
    while pointer < length:
        command = gfxData[pointer]
        match command:
            case 0x00:
                print(f'Zero. End of a line!')
                lines.append(newGfxBytes)
                pointer += 1
            case 0x40:
                newGfxBytes += b'' * width
                pointer += 1
            case 0x80:
                newGfxBytes += b'' * width
                pointer += 1
            case _:
                print(f'Case not 0x0, 0x40, 0x80')
                if command < 0x80:
                    print(f'adding {command} bytes in front...')
                    dataToAdd = gfxData[pointer + 1: pointer + 1 + command]
                    newGfxBytes += dataToAdd
                    pointer += command + 1
                elif command > 0x80:
                    numBytesToAdd = command - 0x80
                    position = 0 - gfxData[pointer + 1]
                    print(f'Repeating {command} bytes behind...')
                    bytesToRepeat = newGfxBytes[position:position + numBytesToAdd]
                    print(bytesToRepeat.hex())
                    newGfxBytes += bytesToRepeat
                    pointer += 2

    return newGfxBytes

