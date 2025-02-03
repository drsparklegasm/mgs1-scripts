"""
This is a testing script for developing a tool for working with STAGE.DIR
"""

import os, re, glob, struct

extTable = { # From jayveer's REX utility: https://github.com/Jayveer/Rex/blob/master/mgs/common/ext_table.h
    0x62: "bin",
    0x63: "con",
    0x64: "dar",
    0x65: "efx",
    0x67: "gcx",
    0x68: "hzm",
    0x69: "img",
    0x6B: "kmd",
    0x6C: "lit",
    0x6D: "mdx",
    0x6F: "oar",
    0x70: "pcx",
    0x72: "rar",
    0x73: "sgt",
    0x77: "wvx",
    0x7A: "zmd",
    0xFF: "noFile" # End of the C family grouping
}

# First thing is to figure out a working Table of Contents, then we can work at making and splitting directories.

filename = 'build/usa-d1/MGS/STAGE.DIR'
stageData = open(filename, 'rb').read()
debug = True

"""
class tableContents:
    size = struct.unpack("I", stageData[0:4])[0]

"""

class stageContents:
    name: str
    """
    data start/end is given in blocks of 0x800
    """
    startBlock: int
    endBlock: int
    binaryData: bytes

    files = [] # List of stageFile class objects, each is a file in the stage data.

    """
    Not sure if this will work?
    """
    def getFiles(self):
        self.files = getStageFiles(self.binaryData[0:0x800])

class stageFile:
    """
    An individual file in a stage. Should have the info
    needed to extract on a per-file basis if warranted.
    """
    nameChecksum: bytes
    fileFamily: int
    fileType: int
    # offset: int # I don't think this is used. use start instead. 
    startBlock: int # This is the block where the file starts, where each block is 0x800 and first block is TOC
    start: int # Offset (relative to the stage)
    end: int # start + size
    size: int # size of file (bytes)
    filename: str

    # Repacking info. 
    numBlocks: int # returns 0 if this is a c family!

    def getFilename(self) -> str:
        self.filename = f'{self.nameChecksum}.{extTable.get(self.fileType)}'
        return self.filename

    def getBlocks(self):
        if self.fileFamily == 0x63:
            self.numBlocks = 0
        else:
            self.numBlocks = self.size // 0x800 + 1
    
    def __str__(self):
        global filename
        filename = extTable.get(self.fileType)
        printText = f'File: {self.nameChecksum}.{filename}\n\tOffset: {self.start}\n\tSize: {self.size}'
        return printText
    
def getStagesInBin():
    global stageData

    size = struct.unpack("I", stageData[0:4])[0]
    tableOfConts = {} # List of stages and their blocks (start, end)
    stageList = []

    offset = 4
    while offset < size:
        newStage = stageContents()
        # Get the data
        stageName = stageData[offset:offset + 8].decode('utf8').rstrip('\x00')
        location = struct.unpack("I", stageData[offset + 8: offset + 12])[0]
        locationEnd = struct.unpack("I", stageData[offset + 20: offset + 24])[0]
        if locationEnd == 0:
            locationEnd = len(stageData) // 0x800

        # Old:
        tableOfConts.update({stageName: (location, locationEnd)})

        # Add attributes to stage object:
        newStage.name = stageName
        newStage.startBlock = location
        newStage.endBlock = locationEnd
        newStage.binaryData = stageData[location * 0X800: locationEnd * 0X800]
        
        # Add to list
        stageList.append(newStage)
        offset += 12
    
    return stageList

allStages = getStagesInBin()

def getStage(name: str):
    global allStages
    for stage in allStages:
        if stage.name == name:
            return stage
    print(f'Error! "{name}" is not a valid stage name! Exiting... ')
    exit(1)

"""for key in tableOfConts.keys():
    print(f'{key}: {tableOfConts.get(key)}')"""

def printStageOffsets() -> None:
    for stage in allStages:
        print(f'{stage.name}: ({stage.startBlock}, {stage.endBlock})')
    return

def extractStageBins():
    """
    Writes individual stage binaries to individual folders/files
    """
    for stage in allStages:
        os.makedirs(f"extractedStage/{stage.name}")
        with open(f'extractedStage/{stage.name}/{stage.name}.bin', 'wb') as f:
            f.write(stage.binaryData)
        print(f'Stage {stage.name} written!')

def getStageFiles(fileListBin: bytes) -> list:
    """
    This gets the list of files in the stage. Alternatively, can be called
    from within the stage 
    """
    offset = 4
    stageFiles = []
    blockOffset = 1 # Always 1, never seen a table of contents longer than 0x800 bytes.

    while offset < len(fileListBin):
        currentFile = stageFile()
        # We can loop to see which type of file we hit and add it. 
        if fileListBin[offset : offset + 8] == bytes(8): # Reached end of the contents
            if debug:
                print(f'Reached end of list! Breaking...')
            break
        elif fileListBin[offset + 2] == 0x63: # Handling C files... 
            stageCFiles = []
            cfileHeaders = []
            while fileListBin[offset + 3] != 0xFF:
                cfileHeaders.append(fileListBin[offset: offset + 8])
                offset += 8
            cfileHeaders.reverse()
            cfileEnd = struct.unpack("I", fileListBin[offset + 4: offset + 8])[0] # Used to track the end of a file, as these are crunched together.
            cFileBlocks = cfileEnd // 0x800 + 1
            for header in cfileHeaders:
                currentCFile = stageFile()
                currentCFile.nameChecksum = header[0:2][::-1].hex()
                currentCFile.fileFamily = header[2]
                currentCFile.fileType = header[3]
                currentCFile.startBlock = blockOffset # Doesnt mean anything for the cfiles.
                # Start, end, size
                currentCFile.end = cfileEnd 
                currentCFile.start = (blockOffset * 0x800) + struct.unpack("I", header[4:8])[0]
                currentCFile.size = (blockOffset * 0x800) + currentCFile.end - currentCFile.start

                # We update this for the next loop
                cfileEnd = currentCFile.start
                # Add to sub list, which is then reversed and added to stageFiles
                stageCFiles.append(currentCFile)

            # Before exiting c family loop, add the total blocks 
            blockOffset += cFileBlocks

            # Add the C files to stage files
            stageCFiles.reverse()
            for file in stageCFiles:
                stageFiles.append(file)
            # Offset stil at the cfile total, ok to add 8 bytes.
        else:  
            tocEntry = fileListBin[offset : offset + 8]
            currentFile.nameChecksum = tocEntry[0:2][::-1].hex()
            currentFile.fileFamily = tocEntry[2]
            currentFile.fileType = tocEntry[3]

            # Now the dicey bits...
            currentFile.size = struct.unpack("I", tocEntry[4:8])[0]
            currentFile.startBlock = blockOffset
            currentFile.start = blockOffset * 0x800
            currentFile.end = currentFile.start + currentFile.size

            # Update the file blocks (blocks is how many blocks of 0x800 size it needs)
            fileBlocks = currentFile.size // 0x800 + 1
            blockOffset += fileBlocks

            # Add to the files list
            stageFiles.append(currentFile)
        # After each file, we increase offset by 8
        offset += 8
    
    # Optional debug output of the file. 
    """if debug: # Took this out for now. 
        for file in stageFiles:
            print(file)"""

    return stageFiles

def printStageFiles():
    for stage in allStages:
        print(stage)


"""
Next step: Write block and file size calcs. 
Then: The file exports on a per-stage basis.
"""

def exportStageFiles(stageName: str, file:str=None) -> None:
    pass

if __name__ == "__main__":

    exportFileData: bytes = None

    stageSelect = input('Which stage do you want to list files from? \n')
    stage = getStage(stageSelect)
    files = getStageFiles(stage.binaryData[0:0x800])
    for file in files:
        print(file)
    fileToExport = input(f'Which file from stage {stageSelect} do you want to export? [ALL exports all files!]\n')

    for file in files:
        file.getFilename()
        if file.filename == fileToExport:
            exportFileData = stage.binaryData[file.start: file.end]
            break
    
    if fileToExport == "ALL":
        i = 0
        for file in files:
            exportFileData = stage.binaryData[file.start: file.end]
            with open(f'extractedStage/{stageSelect}/{stageSelect}-{i:02}-{file.filename}', 'wb') as f:
                f.write(exportFileData)
            f.close()
            i += 1
    elif exportFileData == None: 
        print(f'Export failed! {fileToExport} was not found in stage {stageSelect}! Exiting...')
        exit(2)
    else:
        with open(f'extractedStage/{stageSelect}/{fileToExport}', 'wb') as f:
            f.write(exportFileData)
        f.close()
    
    exit(0)