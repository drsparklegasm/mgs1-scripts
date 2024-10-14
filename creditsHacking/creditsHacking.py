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

creditsFilename = "creditsHacking/00b8ba.rar"
creditsData = open(creditsFilename, 'rb').read()

class imageData:
    
    def __init__(self, allData: bytes):
        self.width = struct.unpack('<H', allData[0:2])[0]
        self.height = struct.unpack('<H', allData[2:4])[0]
        self.palette = allData[4:36]
        self.dataLength = struct.unpack('<L', allData[36:40])[0]
        self.compData = allData[40: 40 + self.dataLength]
        

def decompressBytes(gfxData: bytes, size: tuple [int, int]) -> bytes:
    newGfxBytes = b''
    lines = []
    width, height = size
    length = len(gfxData)
        

    pointer = 0
    while pointer < length:
        command = gfxData[pointer]
        print(f'Command bytes: {gfxData[pointer:pointer+2]}')
        match command:
            case 0x00:
                lines.append(newGfxBytes)
                if len(newGfxBytes) != int(width / 2):
                    print(f'Line did not match! Width: {width}, bytes: {len(newGfxBytes)}. Should be doubled!')
                newGfxBytes = b''
                pointer += 1
            case 0x40:
                newGfxBytes += bytes.fromhex('ff') * int(width / 2)
                lines.append(newGfxBytes)
                newGfxBytes = b''
                pointer += 1
            case 0x80:
                newGfxBytes += bytes.fromhex('00') * int(width / 2)
                lines.append(newGfxBytes)
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
                        bytesToRepeat = newGfxBytes[position:]
                    else:
                        bytesToRepeat = newGfxBytes[position:position + numBytesToAdd]
                    newGfxBytes += bytesToRepeat * int(numBytesToAdd / len(bytesToRepeat))
                    pointer += 2

    print(f'{width} x {height}')
    for line in lines:
        print(f'{len(line)}')
    
    print(f'Height is {height}, we have {len(lines)} lines!')
    return lines

def getImages(fileData: bytes) -> list:
    images = []
    numImg = struct.unpack('<L', fileData[0:4])[0]
    i = 0
    nextImage = 4
    while i < numImg:
        images.append(imageData(fileData[nextImage:]))
        nextImage += images[-1].dataLength + 40
        i += 1
    
    return images

def outputToTGA():
    print(f'Dostufff')

# def analyzeImage(imgData: bytes) -> tuple[bytes, int, int, bytes]:

if __name__ == "__main__":
    print(f'Outputting graphics from {creditsFilename}')
    imageList = getImages(creditsData)
    print(f'{len(imageList)} images found!')
    for image in imageList:
        size = (image.width, image.height)
        lines = decompressBytes(image.compData, size)
        print(f'Color Palette:\n{image.palette.hex()}')
        print(f'Lines: \n')
        for line in lines:
            print(line.hex())
        
    
    