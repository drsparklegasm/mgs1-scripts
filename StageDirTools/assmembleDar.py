import struct
import os
import glob
import argparse

def extract_numeric_prefix(filename):
    # Extract the numeric prefix before the first hyphen
    base_name = os.path.basename(filename)
    prefix = base_name.split('-')[0]
    return int(prefix)

def getHashHex(filename: str) -> str:
    return filename.split('-')[1].split('.')[0]


if __name__ == "__main__":
    darFileName: str
    inputDir: str

    parser = argparse.ArgumentParser(description=f'Creates a dar file from a directory with .pcx files. Ex: assembleDar.py path/to/pcxfiles/ [output.dar]')
    parser.add_argument('input', type=str, help="Folder containing .pcx files to assemble into a DAR.")
    parser.add_argument('filename', type=str, help="Output filename, ex: new-01.dar")

    args= parser.parse_args()

    inputDir = args.input
    darFileName = args.filename

    files = glob.glob(f'{inputDir}/*')

    # Sort the files using the custom key
    files.sort(key=extract_numeric_prefix)

    darBytes = b''

    for file in files:
        # Get header bytes
        fileHeader = getHashHex(os.path.basename(file))
        fileHeadBytes = bytes.fromhex(fileHeader)[::-1]
        print(fileHeadBytes.hex())
        with open(file, 'rb') as f:
            data = f.read()
            f.close()
        darBytes += fileHeadBytes + struct.pack("I", len(data)) + data

    with open(darFileName, 'wb') as f:
        f.write(darBytes)
        f.close