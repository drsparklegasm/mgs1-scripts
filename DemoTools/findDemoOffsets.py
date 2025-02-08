import os, struct
# import progressbar, time

version = "jpn"
filename = f"build-src/{version}-d1/MGS/DEMO.DAT"
outputDir = f"demoWorkingDir/{version}/bins"

demoFile = open(filename, 'rb')
demoData = demoFile.read()

offsets = []
os.makedirs(outputDir, exist_ok=True)
opening = b'\x10\x08\x00\x00'
# opening = b'\x10\x08\x00\x00\x05\x00\x00\x00' the other four bytes may not be needed, TODO: Test this further


def findDemoOffsets():
    offset = 0
    while offset < len(demoData) - 8:
        # print(f'We\'re at {offset}\n')
        checkbytes = demoData[offset:offset + 4]
        if checkbytes == opening:
            print(f'Offset found at offset {offset}!')
            offsets.append(offset)
            offset += 2048 # All demo files are aligned to 0x800, SIGNIFICANTLY faster to do this than +8! Credit to Green Goblin
        else:
            offset += 2048

    print(f'Ending! {len(offsets)} offsets found:')
    for offset in offsets:
        print(offset.to_bytes(4, 'big').hex())

def splitDemoFiles():
    i = 0
    for i in range(len(offsets)):  
        start = offsets[i] 
        if i < len(offsets) - 1:
            end = offsets[i + 1]
        else:
            end = len(demoData) 
        f = open(f'{outputDir}/demo-{i + 1:02}.bin', 'wb')
        f.write(demoData[start:end])
        f.close()
        print(f'Demo {i + 1} written!')
    
    print(f'{len(offsets)} demo files written!')


if __name__ == '__main__':
    findDemoOffsets()
    splitDemoFiles()