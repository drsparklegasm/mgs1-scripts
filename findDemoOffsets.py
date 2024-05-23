import os, struct
# import progressbar, time

filename = "build/MGS/DEMO.DAT"

demoFile = open(filename, 'rb')
demoData = demoFile.read()

offsets = []


opening = b'\x10\x08\x00\x00\x05\x00\x00\x00'
print(opening)
print(demoData[0:8])

def findDemoOffsets():
    offset = 0
    while offset < len(demoData) - 8:
        # print(f'We\'re at {offset}\n')
        checkbytes = demoData[offset:offset + 8]
        if checkbytes == opening:
            print(f'Offset found at offset {offset}!')
            offsets.append(offset)
            offset += 8
        else:
            offset += 8

    print(f'Ending! {len(offsets)} offsets found:')
    for offset in offsets:
        print(offset.to_bytes(4, 'big').hex())

def splitDemoFiles():
    for i in range(len(offsets)):
        if i == len(offsets):
            f = open(f'demo-{i}.txt', 'wb')
            f.write(demoData[offsets[i]:len(demoData)])
            f.close()
        else:   
            f = open(f'demo-{i}.txt', 'wb')
            f.write(demoData[offsets[i]:offsets[i+1]])
            f.close()


if __name__ == '__main__':
    findDemoOffsets()
    splitDemoFiles()