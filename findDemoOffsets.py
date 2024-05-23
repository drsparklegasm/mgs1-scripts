import os, struct
# import progressbar, time

filename = "build-jpn/iso/MGS/DEMO.DAT"

demoFile = open(filename, 'rb')
demoData = demoFile.read()

offsets = []
os.makedirs('extractedDemos', exist_ok=True)
opening = b'\x10\x08\x00\x00\x05\x00\x00\x00'

def findDemoOffsets():
    offset = 0
    while offset < len(demoData) - 8:
        # print(f'We\'re at {offset}\n')
        checkbytes = demoData[offset:offset + 8]
        if checkbytes == opening:
            print(f'Offset found at offset {offset}!')
            offsets.append(offset)
            offset += 2048 # All demo files are a multiple of 0x08000, SIGNIFICANTLY faster to do this than +8! Credit to Green Goblin
        else:
            offset += 2048

    print(f'Ending! {len(offsets)} offsets found:')
    for offset in offsets:
        print(offset.to_bytes(4, 'big').hex())

def splitDemoFiles():
    for i in range(len(offsets)):  
        start = offsets[i] 
        if i < len(offsets) - 1:
            end = offsets[i + 1]
        else:
            end = len(demoData) - 1
        f = open(f'extractedDemos/demo-{i + 1}.bin', 'wb')
        f.write(demoData[start:end])
        f.close()
        print(f'Demo {i + 1} written!')
    
    print(f'{i+1} demo files written!')


if __name__ == '__main__':
    findDemoOffsets()
    splitDemoFiles()