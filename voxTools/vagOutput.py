from demoClasses import *

if __name__ == "__main__":
    demoData: bytes
    # Add in and out file names here
    demoFilename = "example.vox"
    newFileName = demoFilename.split("/")[-1].split(".")[0] + ".vag"

    with open(demoFilename, "rb") as f:
        demoData = f.read()
        demoItems = parseDemoData(demoData)

    outputVagFile(demoItems, newFileName)