import json

oldVersion = "build-proprietary/demo/demoText-jpn-undub-v2.json"
output = "build-proprietary/demo/demoText-jpn-undub-output.json"

oldData = json.load(open(oldVersion, 'r'))
newData = {}

timing: int
duration: int
blankDict = {}

def convertToNew(oldData: dict) -> dict: # Returns newData format
    newData = {}
    for demo in oldData.keys():
        newData[demo] = {}
        for key in oldData[demo][0].keys():
            timing, duration = oldData[demo][1][key].split(",")
            # print(f"Timing: {timing}, Duration: {duration}, Text: {oldData[demo][0][key]}")
            newData[demo][timing] = {
                "duration": str(duration),
                "text": oldData[demo][0][key]
            }
    
    return newData


"""
A bit of an oversight, but since we've changed formats for the demo json, we need to convert it BACK. 
"""

def convertToOld(newData: dict) -> dict: # Returns oldData format
    oldData = {}
    for demoName in newData.keys(): 
        i = 1
        texts = {}
        timings = {}
        for startFrame in newData[demoName].keys():
            iFormat = f"{i:02}"
            texts.update( {iFormat : newData[demoName][startFrame]["text"]})
            timings.update( {iFormat: f"{startFrame},{newData[demoName][startFrame]["duration"]}"})
            oldData[demoName] = [texts, timings]
            i += 1 
        print(oldData[demoName])
    return oldData

if __name__ == "__main__":
    outputData = convertToOld(oldData)
    with open(output, 'w') as f:
        json.dump(outputData, f, ensure_ascii=False)