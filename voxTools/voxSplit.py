import os

version = 'usa'
version = 'jpn'
disc = 1
filename = f'build-src/{version}-d{disc}/MGS/VOX.DAT'
outputDir = f'voxWorkingDir/{version}-d{disc}/origVox'

demoFile = open(filename, 'rb')
demoData = demoFile.read()

debug = True

offsets = []
os.makedirs(outputDir, exist_ok=True)
opening = b'\x10\x08\x00\x00'  # Adjusted opening pattern

def findDemoOffsets():
    offset = 0
    while offset < len(demoData) - 4:  # Adjusted for the new opening length
        checkbytes = demoData[offset:offset + 4]  # Check the first 4 bytes
        if checkbytes == opening:
            offsets.append(offset)
            offset += 2048  # Continue using 2048 as the increment step for speed
        else:
            offset += 2048

def splitDemoFiles():
    global debug

    for i in range(len(offsets)):  
        start = offsets[i] 
        if i < len(offsets) - 1:
            end = offsets[i + 1]
        else:
            end = len(demoData)  # Include the last byte
        f = open(f'{outputDir}/{i + 1:03}.bin', 'wb')
        f.write(demoData[start:end])
        f.close()
        if debug:
            print(f'Wrote VOX file {i}')

if __name__ == '__main__':
    findDemoOffsets()
    splitDemoFiles()
