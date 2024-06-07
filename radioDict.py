#!/bin/python

import os, struct
import charactersTest as characters

# GLOBAL STUFF
missingChars = open('KanjiStillMissing.txt', 'w')

os.makedirs('graphicsExport', exist_ok=True)
radioData = bytes

class graphicSegment:

	def __init__(self, offset, callGraphicNum, graphicBytesHex) -> None:
		self.callOffset = offset
		self.indexNum = callGraphicNum
		self.bytesHex = graphicBytesHex
		pass

	def __str__(self):
		return f'{self.callOffset}, {self.indexNum}, {self.bytesHex}'

foundGraphics = []

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

def makeCallDictionary(graphicsBytes: bytes):
	"""
	Returns a DICT specific to the call where we sent the data. 
	"""
	charDict = {}
	if len(graphicsBytes) % 36 != 0:
		print(f'Error! LENGTH is not even number of graphics!')
	else:
		count = 0 # May need to start at 1 instead
		callDictionary = {}
		if len(graphicsBytes) % 36 == 0:
			count = int(len(graphicsBytes) / 36)
			for x in range(count):
				segment = graphicsBytes[x * 36: (x + 1) * 36 ]
				result = characters.graphicsData.get(segment.hex())
				callDictionary.update({x + 1: result})
		return callDictionary

openRadioFile('Radio dat files/RADIO-jpn-d1.DAT')
# outputManyGraphics()

def translateJapaneseHex(bytestring: bytes, callDict: dict[str, str] ) -> str: # Needs fixins, maybe move to separate file?
	i = 0
	messageString = ''
	while i < len(bytestring) - 1:
		# print(f'i is {i}\n') # For debugging
		if bytestring[i].to_bytes() == b'\x96':
			try:
				messageString += callDict.get(int(bytestring[i + 1]))
			except:
				# print(f'Cound not translate {bytestring[i + 1]}')
				messageString += f'{bytestring[i:i+2].hex()}'
			i += 2
		else:
			# print(f'i = {i}, category: {bytestring[i].to_bytes()} byte = {bytestring[i+1].to_bytes().hex()}')
			if bytestring[i] < 0x80:
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
					print(f'Unable to translate Japanese byte code {bytestring[i : i + 2].hex()}!!!\n')
					missingChars.write(f'[{bytestring[i : i + 2].hex()}]\n')
					messageString += f'[{bytestring[i : i + 2].hex()}]'
			i += 2
	return messageString

"""
This only used for working with the graphics data found in jpn-d1, it was combined with the bash script to ocr the characters
"""

def exportuniquegraphics():
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
	

# exportuniquegraphics()

# Testing the dictionary writing with the graphics data after 140.85



# TESTING! : 

# Use this to test all characters in a radio call
"""campbellDict = makeCallDictionary(bytes.fromhex('0a0b000eaba92dfffe3c0e00bc2c003c3ffc2cbae82ed2c02c42c02c6ae92cbffe0000003febfc3aebac3aebac3febfc3aaa6c3aeb6c3aff2c3aeb2c3aeb2c3bffac380bb80000000038002ffff02eaab02ffff02eaab02eaab02ffff02c2db42c0be06ef2e9bea06c0000000e0aa80e0ffc3fe0282ee0b42de0e03aeffe3adae91f80e00bd0e07ea6e02413d000000028bffc1ebaac25b02c78b02c1dbffc006ee80a2ce00e38e02db4e97ae0ee2580bd000000003800003800003800003800003ff0003aa00038000038000038006abaa9bffffe000000002c00002c003ffffc3aaeac382c2c382c2c3ffffc3aaeac242c18002c00002c00000000002c00002c000ffff00eaeb00e2cb06eaeb9bffffe00be0006eb906f81f92900680000002ffff82eaab82ffff82eaab82ffff81ab4900fe8e06aeae9bffffe1bc0e00e40e0000000bf9ea4bbbeb8b757a0ba6ff9ba3aacb76ae8b3aee8b7aee9bbbffeb502c0b002c00000000fffe00aabd000ab40007d00bffffe6abaad00387800382400380002b80002f40000000026fff879baf429afe802ebac6afffcbeebac2eebac2e8b7c2e4624bbfffd20aaa8000000002c002c2c382c2c382eaeb82ffff8002c00382c2c382c2c3aaeac3ffffc38002c0000000d0e006c2ffcbabeb83f5bb42e4be47eaebdbeeaa82a6ffc7bac2caaeffc5eaeac0000002ffffc2eaeac2effec2daeac2effec2daaac2effec3aeaec3affecb5aaec2000b80000001d02c00bbffe22baee78b2c91dbffc00bbac0abb280eb7b42da2e078ebf9246e2c0000002396806bb6c0bffbfe2efbad77abac0746a8bffaf86eb4f07da2f86febad39ba480000002c3ffc2c3aac2c3ffcbf3aac6e2aa82cbffe2c2ea92fbaeebe2edea42aee00077800000000280000be0002d7801b41e47effbd11aa440aaaa00ffff00e00b00ffff00eaab00000000038003ffffc2aeba86aeba9bffffe0aaaa00ffff00eaab00eaab00ffff00eaab0000000002ba8bfbaacbbbffcb3baacb3baa8b3bffeb3baa9bbbffebfa59eb07aee00baed0000003ffffc2baae80baae00bffe00b00e00bffe00baae00b00e96bfffebeaae00000e0000000002c00002c00002c00052c500b2ce01e2cb42c2c38782c2d102c0401ac0000f8000000000ffff00eaab00ebff06ebab9baaaaebbffee0baae00baae00bffe00b06e00b03d00000006aaea9bffffe26aea03bfff03baab03baab03bfff03baab03aaaa03ffffe3aaaa90000000e3ffe0e3aa9bfbaa86e7bfc0e38000fbffebe7bb96e3bba0e77b86eb7ed3d2b880000007728ec3bb8ee2ab8e93ffffe3baee83baced3ffcf82ba8b4bffcf96baafe038268000000'))
for x in range(len(campbellDict)):
	print(f'{campbellDict.get(x)}')"""


# translatedText = translateJapaneseHex(bytes.fromhex('8144 812f 814a d002 906a 9606 8138 812e 824b d006 8228 812f 9607 9608 812e 9609 960a 906e 5c72 5c6e 8120 8111 8149 8117 8104 d003 00'), '0a0b000eaba92dfffe3c0e00bc2c003c3ffc2cbae82ed2c02c42c02c6ae92cbffe0000003febfc3aebac3aebac3febfc3aaa6c3aeb6c3aff2c3aeb2c3aeb2c3bffac380bb80000000038002ffff02eaab02ffff02eaab02eaab02ffff02c2db42c0be06ef2e9bea06c0000000e0aa80e0ffc3fe0282ee0b42de0e03aeffe3adae91f80e00bd0e07ea6e02413d000000028bffc1ebaac25b02c78b02c1dbffc006ee80a2ce00e38e02db4e97ae0ee2580bd000000003800003800003800003800003ff0003aa00038000038000038006abaa9bffffe000000002c00002c003ffffc3aaeac382c2c382c2c3ffffc3aaeac242c18002c00002c00000000002c00002c000ffff00eaeb00e2cb06eaeb9bffffe00be0006eb906f81f92900680000002ffff82eaab82ffff82eaab82ffff81ab4900fe8e06aeae9bffffe1bc0e00e40e0000000bf9ea4bbbeb8b757a0ba6ff9ba3aacb76ae8b3aee8b7aee9bbbffeb502c0b002c00000000fffe00aabd000ab40007d00bffffe6abaad00387800382400380002b80002f40000000026fff879baf429afe802ebac6afffcbeebac2eebac2e8b7c2e4624bbfffd20aaa8000000002c002c2c382c2c382eaeb82ffff8002c00382c2c382c2c3aaeac3ffffc38002c0000000d0e006c2ffcbabeb83f5bb42e4be47eaebdbeeaa82a6ffc7bac2caaeffc5eaeac0000002ffffc2eaeac2effec2daeac2effec2daaac2effec3aeaec3affecb5aaec2000b80000001d02c00bbffe22baee78b2c91dbffc00bbac0abb280eb7b42da2e078ebf9246e2c0000002396806bb6c0bffbfe2efbad77abac0746a8bffaf86eb4f07da2f86febad39ba480000002c3ffc2c3aac2c3ffcbf3aac6e2aa82cbffe2c2ea92fbaeebe2edea42aee00077800000000280000be0002d7801b41e47effbd11aa440aaaa00ffff00e00b00ffff00eaab00000000038003ffffc2aeba86aeba9bffffe0aaaa00ffff00eaab00eaab00ffff00eaab0000000002ba8bfbaacbbbffcb3baacb3baa8b3bffeb3baa9bbbffebfa59eb07aee00baed0000003ffffc2baae80baae00bffe00b00e00bffe00baae00b00e96bfffebeaae00000e0000000002c00002c00002c00052c500b2ce01e2cb42c2c38782c2d102c0401ac0000f8000000000ffff00eaab00ebff06ebab9baaaaebbffee0baae00baae00bffe00b06e00b03d00000006aaea9bffffe26aea03bfff03baab03baab03bfff03baab03aaaa03ffffe3aaaa90000000e3ffe0e3aa9bfbaa86e7bfc0e38000fbffebe7bb96e3bba0e77b86eb7ed3d2b880000007728ec3bb8ee2ab8e93ffffe3baee83baced3ffcf82ba8b4bffcf96baafe038268000000')
# print(translatedText)


