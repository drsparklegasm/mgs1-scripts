import demoTextExtractor as DTE
import re, struct

inputFile = 'demoWorkingDir/jpn/bins/demo-6.bin'
demoFile = open(inputFile, 'rb')
demoData = demoFile.read()


