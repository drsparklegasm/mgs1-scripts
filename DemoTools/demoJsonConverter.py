import json

oldVersion = "build-proprietary/demo/demoText-jpn-undub.json"
output = "build-proprietary/demo/demoText-jpn-undub-newFormat.json"

oldData = json.load(open(oldVersion, 'r'))

newData = {}

timing: int
duration: int
blankDict = {}

for demo in oldData.keys():
    newData[demo] = {}
    for key in oldData[demo][0].keys():
        timing, duration = oldData[demo][1][key].split(",")
        # print(f"Timing: {timing}, Duration: {duration}, Text: {oldData[demo][0][key]}")
        newData[demo][timing] = {
            "duration": str(duration),
            "text": oldData[demo][0][key]
        }

with open(output, 'w') as f:
    json.dump(newData, f, ensure_ascii=False)