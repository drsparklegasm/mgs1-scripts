"""
Simple script that exports all .pcx images in a .dar archive.
"""
import struct
import os
import argparse

def parse_dar_file(file_path, output_dir):
    with open(file_path, 'rb') as f:
        # Read and parse the header (example assumes header contains number of files)
        num_files = struct.unpack('<I', f.read(4))[0]  # Assuming little-endian unsigned int

        file_entries = []
        for _ in range(num_files):
            # Read each file entry's metadata
            # Example assumes each entry has a 4-byte offset and 4-byte size
            offset = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<I', f.read(4))[0]
            file_entries.append((offset, size))

        for i, (offset, size) in enumerate(file_entries):
            f.seek(offset)
            file_data = f.read(size)
            output_file_path = os.path.join(output_dir, f'file_{i}')
            with open(output_file_path, 'wb') as out_file:
                out_file.write(file_data)

# Usage
# parse_dar_file('/home/solidmixer/projects/mgs1-undub/extractedStage/s00a/0000.dar', '/home/solidmixer/projects/mgs1-undub/extractedStage/s00a/')
# darFileName = input(f'What dar file should I extract? ')

darFileName = 'extractedStage/s00a/s00a-02-0000.dar'

if __name__ == "__main__":
    darFileName: str
    outputDir: str

    parser = argparse.ArgumentParser(description=f'Extracts textures in a .dar file. Ex: extractDar.py [example.dar] [output.dir]')

    parser.add_argument('filename', type=str, help="the Dar file to extract.")
    parser.add_argument('outputDir', nargs="?", type=str, help="Output directory")

    args = parser.parse_args()

    darFileName = args.filename

    darData = open(darFileName, 'rb').read()

    if args.outputDir == None:
        outputDir = f'{os.path.dirname(darFileName)}/{os.path.basename(darFileName).split(".")[0]}'
        os.makedirs(outputDir, exist_ok=True)
    else:
        outputDir = args.outputDir
        os.makedirs(outputDir, exist_ok=True)

    offset = 0
    i = 1

    while offset < len(darData):
        # Filename 
        fileName = darData[offset: offset + 4][::-1].hex()
        print(f'{i:02}-{fileName} written!')
        # Get the file
        nextFileSize = struct.unpack("<I", darData[offset + 4: offset + 8])[0]
        offset += 8
        with open(f'{outputDir}/{i:03}-{fileName}.pcx', 'wb') as f:
            f.write(darData[offset: offset + nextFileSize])
            f.close()
        # Print the "in between"
        offset += nextFileSize
        i += 1