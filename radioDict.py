#!/bin/python

import os, struct
import characters as characters

# GLOBAL STUFF
os.makedirs('graphicsExport', exist_ok=True)
missingChars = open('graphicsExport/KanjiStillMissing.txt', 'w')
missingGFX = open('graphicsExport/KanjiStillMissing.txt', 'w')
radioData = b''
foundGraphics = []
unidentifiedGraphics = []

context = open("graphicsExport/contextList.txt", 'w')

class graphicSegment:

	def __init__(self, offset, callGraphicNum, graphicBytesHex) -> None:
		self.callOffset = offset
		self.indexNum = callGraphicNum
		self.bytesHex = graphicBytesHex
		pass

	def __str__(self):
		return f'{self.callOffset}, {self.indexNum}, {self.bytesHex}'

def openRadioFile(filename: str) -> None:
	global radioData
	radioFile = open(filename, 'rb')
	radioData = radioFile.read()

def countGraphics(message: str) -> None:
	count = 0
	for phrase in characters.graphicsData:
		if phrase in message:
			print(f'Phrase {phrase} found!')
			count += 1
	return count

def checkForGraphics(message: str) -> bool:
	for phrase in characters.graphicsData:
		if phrase in message:
			return True	
	return False
					  
def getRadioCharacter(hexString: str) -> str:
	return characters.radioChar[hexString]

def outputEmbeddedGraphics() -> None:
	i = 1
	for data in characters.graphicsData:
		outputGraphic(str(i), bytes.fromhex(data))
		i += 1

def outputManyGraphics(filename: str, data: bytes) -> None:
	count = 0
	if len(data) % 36 == 0:
		count = int(len(data) / 36)
		for x in range(count):
			segment = data[x * 36: (x + 1) * 36 ]
			outputGraphic(f'{filename}-{x}', segment)
			a = graphicSegment(filename, x, segment.hex())
			foundGraphics.append(a)

def outputGraphic(filename: str, file_data: bytes) -> None: 
	"""
	Partially generated from chatGPT but it had the endianness of the width/12 wrong.
	Stolen from https://github.com/metalgeardev/MGS1/blob/master/unRadio_v2.rb and converted by gpt
	"""
	# Convert binary data to bit string
	bit_string = ''.join(format(byte, '08b') for byte in file_data)
	width = len(bit_string) // 2

	with open(f"graphicsExport/{filename}.tga", "wb") as data:
		# Create and write TGA header
		header = "0000020000000000000000000c00" + struct.pack('<H', width // 12).hex() + "2020"
		data.write(bytes.fromhex(header))
		for byte in range(width):
			bits = bit_string[byte * 2 : byte * 2 + 2]
			if bits == "00":
				data.write(bytes.fromhex("000000ff"))
			elif bits == "01":
				data.write(bytes.fromhex("555555ff"))
			elif bits == "10":
				data.write(bytes.fromhex("aaaaaaff"))
			else:
				data.write(bytes.fromhex("ffffffff"))

def makeCallDictionary(offset: int, graphicsBytes: bytes):
	"""
	Returns a DICT specific to the call where we sent the data. 
	"""
	
	# We need to ensure this is evenly divisible by 36 bytes:
	if len(graphicsBytes) % 36 != 0:
		print(f'Error! LENGTH is not even number of graphics! Assuming nulls...')

	count = 0 # May need to start at 1 instead
	callDictionary = {}
	# Output a dictionary file for each dictionary we create
	dictFile = open(f'graphicsExport/Dict-{offset}.txt', 'w')

	# print(len(graphicsBytes))
	count = int(len(graphicsBytes) / 36)
	for x in range(count):
		segment = graphicsBytes[x * 36: (x + 1) * 36 ]

		# This section only necessary if outputtting graphics we haven't identified.
		global foundGraphics
		global unidentifiedGraphics
		if segment.hex() not in characters.graphicsData:
			foundGraphics.append(segment.hex())
			result = f'[{segment.hex()}]'
		elif characters.graphicsData.get(segment.hex()) == "?":
			unidentifiedGraphics.append(segment.hex())
			result = f'[{segment.hex()}]'
		else:
			result = characters.graphicsData.get(segment.hex())

		callDictionary.update({x + 1: result})
		dictFile.write(f'{x + 1}: {result}\n')

	return callDictionary

def translateJapaneseHex(bytestring: bytes, callDict: dict[str, str] ) -> str: # Needs fixins, maybe move to separate file?
	i = 0
	messageString = ''
	customCharacter = False
	while i < len(bytestring) - 1:
		# print(f'i is {i}\n') # For debugging
		if bytestring[i].to_bytes() == b'\x96':
			try:
				messageString += callDict.get(int(bytestring[i + 1]))
			except:
				# print(f'Cound not translate {bytestring[i + 1]}')
				messageString += f'[{bytestring[i:i+2].hex()}]'
				customCharacter = True
			i += 2
		else:
			# print(f'i = {i}, category: {bytestring[i].to_bytes()} byte = {bytestring[i+1].to_bytes().hex()}')
			if bytestring[i] in [0x1f, 0x12]:
				charcheck = bytestring[i:i+2].hex()
				messageString += characters.spanishChars.get(charcheck)
			elif bytestring[i] < 0x80:
				messageString += chr(bytestring[i])
				i -= 1
			elif bytestring[i:i+4] == b'\x5c\x72\x5c\x6e':
				messageString += '\\r\\n'
				i += 2
			elif bytestring[i] in (0x80, 0xC0):
				messageString += characters.radioChar.get(bytestring[i+1].to_bytes().hex())
			elif bytestring[i] in (0x81, 0xC1):
				messageString += characters.hiragana.get(bytestring[i+1].to_bytes().hex())
			elif bytestring[i] in (0x82, 0xC2):
				messageString += characters.katakana.get(bytestring[i+1].to_bytes().hex())
			elif bytestring[i] == 0xd0:
				messageString += characters.punctuation.get(bytestring[i+1].to_bytes().hex())
			else:
				try:
					messageString += characters.kanji.get(bytestring[i:i+2].hex())
				except:
					# print(f'Unable to translate Japanese byte code {bytestring[i : i + 2].hex()}!!!\n')
					missingChars.write(f'[{bytestring[i : i + 2].hex()}]\n')
					messageString += f'[{bytestring[i : i + 2].hex()}]'
					customCharacter = True
			i += 2
	
	if customCharacter == True:
		context.write(f'{messageString}\n')
	return messageString

"""
This only used for working with the graphics data found in jpn-d1, it was combined with the bash script to ocr the characters
"""

def debugExportUniqueGFX():
	uniqueGraphics = open("translation/unique graphics", 'r')
	uniqueGraphics2 = open("translation/unique graphics 2.csv", 'w')
	lineNum = 1
	for line in uniqueGraphics:
		f = open(f'graphicsExport/output/{lineNum}.txt', 'r')
		content = f.read().replace('\n', ' ').strip()
		uniqueGraphics2.write(f'{lineNum}, \"{line.strip()}\", \"{content}\"\n')
		lineNum += 1
		f.close()
	uniqueGraphics2.close()

"""
TESTING AREA! Anything below this is meant for testing functionality or debug. 

"""


"""if __name__ == '__main__':
	# Use this to test all characters in a radio call
	test = open('26213.bin', 'rb')
	testbytes = test.read()
	testingDict = makeCallDictionary(testbytes)
	outputManyGraphics("test", testbytes)

	for x in range(len(testingDict) + 1):
		print(f'{x} = {testingDict.get(x)}', end=" ")"""
"""
data = open('unknownGraphics.txt', 'r')
i = 1
for line in data.readlines():
	line = line.strip()
	outputGraphic(f'unkownChar-{i}', bytes.fromhex(line))
	i += 1
"""