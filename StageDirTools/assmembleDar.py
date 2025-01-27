import struct
import os
import glob


def extract_numeric_prefix(filename):
    # Extract the numeric prefix before the first hyphen
    base_name = os.path.basename(filename)
    prefix = base_name.split('-')[0]
    return int(prefix)

def getHashHex(filename: str) -> str:
    return filename.split('-')[1].split('.')[0]

inputDir = 'extractedDar'
files = glob.glob(f'{inputDir}/*')

# Sort the files using the custom key
files.sort(key=extract_numeric_prefix)

darBytes = b''

for file in files:
    # Get header bytes
    fileHeader = getHashHex(file)
    fileHeadBytes = bytes.fromhex(fileHeader)[::-1]
    print(fileHeadBytes.hex())
    with open(file, 'rb') as f:
        data = f.read()
        f.close()
    darBytes += fileHeadBytes + struct.pack("I", len(data)) + data

with open('extractedDar/outputDar.dar', 'wb') as f:
    f.write(darBytes)
    f.close