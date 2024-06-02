#!/bin/python

import os, struct
import uniqueGraphics as characters

# GLOBAL STUFF

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

radioChar = {
	'd002': "、",
	'd003': "。",
	'd006': "ー",
	'd017': "...", # may need to see if there's an equivelant symbol for this to keep character consistency
	'824f': "0",
	'8250': "1",
	'8251': "2",
	'8252': "3",
	'8253': "4",
	'8254': "5",
	'8255': "6",
	'8256': "7",
	'8257': "8",
	'8258': "9",
	'8260': "A",
	'8261': "B",
	'8262': "C",
	'8263': "D",
	'8264': "E",
	'8265': "F",
	'8266': "G",
	'8267': "H",
	'8268': "I",
	'8269': "J",
	'826a': "K",
	'826b': "L",
	'826c': "M",
	'826d': "N",
	'826e': "O",
	'826f': "P",
	'8270': "Q",
	'8271': "R",
	'8272': "S",
	'8273': "T",
	'8274': "U",
	'8275': "V",
	'8276': "W",
	'8277': "X",
	'8278': "Y",
	'8279': "Z",
	'827a': "[",
	'827b': "\\",
	'827c': "]",
	'827d': "^",
	'827e': "_",
	'827f': "`",
	'8281': "a",
	'8282': "b",
	'8283': "c",
	'8284': "d",
	'8285': "e",
	'8286': "f",
	'8287': "g",
	'8288': "h",
	'8289': "i",
	'828a': "j",
	'828b': "k",
	'828c': "l",
	'828d': "m",
	'828e': "n",
	'828f': "o",
	'8290': "p",
	'8291': "q",
	'8292': "r",
	'8293': "s",
	'8294': "t",
	'8295': "u",
	'8296': "v",
	'8297': "w",
	'8298': "x",
	'8299': "y",
	'829a': "z",
	'8030': "０",
	'8031': "１",
	'8032': "２",
	'8033': "３",
	'8034': "４",
	'8035': "５",
	'8036': "６",
	'8037': "７",
	'8038': "８",
	'8039': "９",
	'803a': "：",
	'803b': "；",
	'803c': "＜",
	'803d': "＝",
	'803e': "＞",
	'803f': "？",
	'8040': "²",
	'8041': "Ａ",
	'8042': "Ｂ",
	'8043': "Ｃ",
	'8044': "Ｄ",
	'8045': "Ｅ",
	'8046': "Ｆ",
	'8047': "Ｇ",
	'8048': "Ｈ",
	'8049': "Ｉ",
	'804a': "Ｊ",
	'804b': "Ｋ",
	'804c': "Ｌ",
	'804d': "Ｍ",
	'804e': "Ｎ",
	'804f': "Ｏ",
	'8050': "Ｐ",
	'8051': "Ｑ",
	'8052': "Ｒ",
	'8053': "Ｓ",
	'8054': "Ｔ",
	'8055': "Ｕ",
	'8056': "Ｖ",
	'8057': "Ｗ",
	'8058': "Ｘ",
	'8059': "Ｙ",
	'805a': "Ｚ",
	'805b': "［",
	'805c': "＼",
	'805d': "］",
	'805e': "＾",
	'805f': "＿",
	'8060': "｀",
	'8061': "ａ",
	'8062': "ｂ",
	'8063': "ｃ",
	'8064': "ｄ",
	'8065': "ｅ",
	'8066': "ｆ",
	'8067': "ｇ",
	'8068': "ｈ",
	'8069': "ｉ",
	'806a': "ｊ",
	'806b': "ｋ",
	'806c': "ｌ",
	'806d': "ｍ",
	'806e': "ｎ",
	'806f': "ｏ",
	'8070': "ｐ",
	'8071': "ｑ",
	'8072': "ｒ",
	'8073': "ｓ",
	'8074': "ｔ",
	'8075': "ｕ",
	'8076': "ｖ",
	'8077': "ｗ",
	'8078': "ｘ",
	'8079': "ｙ",
	'807a': "ｚ",
	'807b': "{",
	'807c': "\r",
	'807d': "}",
	'807e': "¹",
	'8102': "あ",
	'8104': "い",
	'8106': "う",
	'8108': "え",
	'810a': "お",
	'810b': "か",
	'810c': "が",
	'810d': "き",
	'810f': "く",
	'8111': "け",
	'8113': "こ",
	'8114': "ご",
	'8115': "さ",
	'8117': "し",
	'8118': "じ",
	'8119': "す",
	'811b': "せ",
	'811d': "そ",
	'811e': "ぞ",
	'811f': "た",
	'8120': "だ",
	'8121': "ち",
	'8124': "つ",
	'8126': "て",
	'8127': "で",
	'8128': "と",
	'8129': "ど",
	'812a': "な",
	'812b': "に",
	'812d': "ね",
	'812e': "の",
	'812f': "は",
	'8130': "ば",
	'8136': "ぶ",
	'813e': "ま",
	'813f': "み",
	'8141': "め",
	'8142': "も",
	'8144': "や",
	'8148': "よ",
	'8149': "ら",
	'814a': "り",
	'814b': "る",
	'814c': "れ",
	'814d': "ろ",
	'814f': "わ",
	'8152': "を",
	'8153': "ん",
	'8201': "ァ", # Katakana start
	'8202': "ア",
	'8203': "ィ",
	'8204': "イ",
	'8205': "ゥ",
	'8206': "ウ",
	'8207': "ェ",
	'8208': "エ",
	'8209': "ォ",
	'820a': "オ",
	'820b': "カ",
	'820c': "ガ",
	'820d': "キ",
	'820e': "ギ",
	'820f': "ク",
	'8210': "グ",
	'8211': "ケ",
	'8212': "ゲ",
	'8213': "コ",
	'8214': "ゴ",
	'8215': "サ",
	'8216': "ザ",
	'8217': "シ",
	'8218': "ジ",
	'8219': "ス",
	'821a': "ズ",
	'821b': "セ",
	'821c': "ゼ",
	'821d': "ソ",
	'821e': "ゾ",
	'821f': "タ",
	'8220': "ダ",
	'8221': "チ",
	'8222': "ヂ",
	'8223': "ッ",
	'8224': "ツ",
	'8225': "ヅ",
	'8226': "テ",
	'8227': "デ",
	'8228': "ト",
	'8229': "ド",
	'822a': "ナ",
	'822b': "ニ",
	'822c': "ヌ",
	'822d': "ネ",
	'822e': "ノ",
	'822f': "ハ",
	'8230': "バ",
	'8231': "パ",
	'8232': "ヒ",
	'8233': "ビ",
	'8234': "ピ",
	'8235': "フ",
	'8236': "ブ",
	'8237': "プ",
	'8238': "ヘ",
	'8239': "ベ",
	'823a': "ペ",
	'823b': "ホ",
	'823c': "ボ",
	'823d': "ポ",
	'823e': "マ",
	'823f': "ミ",
	'8240': "ム",
	'8241': "メ",
	'8242': "モ",
	'8243': "ャ",
	'8244': "ヤ",
	'8245': "ュ",
	'8246': "ユ",
	'8247': "ョ",
	'8248': "ヨ",
	'8249': "ラ",
	'824a': "リ",
	'824b': "ル",
	'824c': "レ",
	'824d': "ロ",
	'824e': "ワ",
	'824f': "ヲ",
	'8253': "ン",
	'9001': "　",
	'9007': "～",
	'9016': "／",
	'901b': "◯",
	'9022': "眼",
	'9026': "行",
	'9028': "漢",
	'9029': "谷",
	'902a': "我",
	'902b': "保",
	'902c': "存",
	'902d': "庫",
	'902e': "大",
	'902f': "雪",
	'9030': "原",
	'9034': "見",
	'9035': "赤",
	'9036': "外",
	'9037': "線",
	'9038': "熱",
	'903b': "体",
	'903d': "別",
	'903f': "毒",
	'9043': "誠",
	'9044': "調",
	'9048': "使",
	'9049': "用",
	'904c': "迷",
	'904d': "彩",
	'9051': "力",
	'9052': "回",
	'9054': "關",
	'9058': "止",
	'905c': "定",
	'905f': "温",
	'9060': "度",
	'9061': "形",
	'9062': "状",
	'9063': "変",
	'9068': "明",
	'906a': "地",
	'906c': "探",
	'906e': "携",
	'9072': "納",
	'9073': "長",
	'907b': "押",
	'907e': "発",
	'9080': "連",
	'9082': "被",
	'9085': "彈",
	'9086': "前",
	'9087': "方",
	'9089': "無",
	'908e': "字",
	'908f': "操",
	'9090': "作",
	'9091': "対",
	'9094': "備",
	'9095': "照",
	'9097': "移",
	'9098': "動",
	'9099': "人",
	'909b': "向",
	'909d': "設",
	'90a2': "楓",
	'90a4': "界",
	'90a6': "電",
	'90a7': "子",
	'90aa': "狙",
	'90ab': "撃",
	'90ac': "入",
	'90ad': "応",
	'90b5': "息",
	'90ba': "頭",
	'90bb': "棟",
	'90c1': "器",
	'90c3': "場",
	'90c4': "所",
	'90c6': "事",
	'90c7': "周",
	'90ca': "生",
	'90cb': "兵",
	'90cc': "戦",
	'90cd': "中",
	'90ce': "少",
	'90d5': "者",
	'90dc': "時",
	'90de': "合",
	'90e3': "一",
	'90e4': "間",
	'90e8': "解",
	'90f0': "彼",
	'90f1': "女",
	'90f5': "冷",
	'90f6': "却",
	'90f9': "抜",
	'90fc': "畿",
	'90fe': "特",
	'9108': "了",
	'9109': "失",
	'9111': "期",
	'910b': "上",
	'9a01': "始",
	'9a02': "到",
	'9a04': "終",
	'9a05': "車",
	'9a03': "音",
	'9a06': "格",
	'9a07': "二",
	'9a08': "階",
	'9a09': "渡",
	'9a0a': "局",
	'9a0b': "救",
	'9a0c': "出",
	'9a0d': "下",
	'9a0f': "独",
	'9a10': "房",
	'9a11': "闘",
	'9a12': "各",
	'9a13': "承",
	'9a14': "武",
	'9a15': "部",
	'9a16': "易",
	'9a17': "通",
	'9a18': "信",
	'9a19': "味",
	'9a1a': "死",
	'9a1c': "三",
	'9a1b': "廊",
	'9a1d': "忍",
	'9a1e': "登",
	'9a1f': "再",
	'9a20': "会",
	'9a21': "便",
	'9a22': "室",
	'9a23': "犬",
	'9a24': "洞",
	'9a25': "窟",
	'9a26': "路",
	'9a27': "目",
	'9a28': "勝",
	'9a29': "利",
	'9a2a': "持",
	'9a2b': "問",
	'9a2c': "脱",
	'9a2d': "想",
	'9a2e': "浦",
	'9a2f': "躍",
	'9a30': "遇",
	'9a31': "墜",
	'9a32': "後",
	'9a33': "溶",
	'9a34': "鉱",
	'9a35': "号",
	'9a36': "点",
	'9a37': "巣",
	'9a38': "鍵",
	'9a39': "紛",
	'9a3a': "司",
	'9a3b': "令",
	'9a3c': "取",
	'9a3d': "得",
	'9a3e': "常",
	'9a3f': "未",
	'9a40': "済",
}

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
					  
def getRadioChar(hexString):
	return radioChar[hexString]

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
		print(f'Error! LENGTH is not even number of graphics! ')
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

def translateJapaneseHex(bytestring: bytes) -> str: # Needs fixins, maybe move to separate file?
	i = 0
	messageString = ''
	callDict = makeCallDictionary(bytes.fromhex('0a0b000eaba92dfffe3c0e00bc2c003c3ffc2cbae82ed2c02c42c02c6ae92cbffe0000003febfc3aebac3aebac3febfc3aaa6c3aeb6c3aff2c3aeb2c3aeb2c3bffac380bb80000000038002ffff02eaab02ffff02eaab02eaab02ffff02c2db42c0be06ef2e9bea06c0000000e0aa80e0ffc3fe0282ee0b42de0e03aeffe3adae91f80e00bd0e07ea6e02413d000000028bffc1ebaac25b02c78b02c1dbffc006ee80a2ce00e38e02db4e97ae0ee2580bd000000003800003800003800003800003ff0003aa00038000038000038006abaa9bffffe000000002c00002c003ffffc3aaeac382c2c382c2c3ffffc3aaeac242c18002c00002c00000000002c00002c000ffff00eaeb00e2cb06eaeb9bffffe00be0006eb906f81f92900680000002ffff82eaab82ffff82eaab82ffff81ab4900fe8e06aeae9bffffe1bc0e00e40e0000000bf9ea4bbbeb8b757a0ba6ff9ba3aacb76ae8b3aee8b7aee9bbbffeb502c0b002c00000000fffe00aabd000ab40007d00bffffe6abaad00387800382400380002b80002f40000000026fff879baf429afe802ebac6afffcbeebac2eebac2e8b7c2e4624bbfffd20aaa8000000002c002c2c382c2c382eaeb82ffff8002c00382c2c382c2c3aaeac3ffffc38002c0000000d0e006c2ffcbabeb83f5bb42e4be47eaebdbeeaa82a6ffc7bac2caaeffc5eaeac0000002ffffc2eaeac2effec2daeac2effec2daaac2effec3aeaec3affecb5aaec2000b80000001d02c00bbffe22baee78b2c91dbffc00bbac0abb280eb7b42da2e078ebf9246e2c0000002396806bb6c0bffbfe2efbad77abac0746a8bffaf86eb4f07da2f86febad39ba480000002c3ffc2c3aac2c3ffcbf3aac6e2aa82cbffe2c2ea92fbaeebe2edea42aee00077800000000280000be0002d7801b41e47effbd11aa440aaaa00ffff00e00b00ffff00eaab00000000038003ffffc2aeba86aeba9bffffe0aaaa00ffff00eaab00eaab00ffff00eaab0000000002ba8bfbaacbbbffcb3baacb3baa8b3bffeb3baa9bbbffebfa59eb07aee00baed0000003ffffc2baae80baae00bffe00b00e00bffe00baae00b00e96bfffebeaae00000e0000000002c00002c00002c00052c500b2ce01e2cb42c2c38782c2d102c0401ac0000f8000000000ffff00eaab00ebff06ebab9baaaaebbffee0baae00baae00bffe00b06e00b03d00000006aaea9bffffe26aea03bfff03baab03baab03bfff03baab03aaaa03ffffe3aaaa90000000e3ffe0e3aa9bfbaa86e7bfc0e38000fbffebe7bb96e3bba0e77b86eb7ed3d2b880000007728ec3bb8ee2ab8e93ffffe3baee83baced3ffcf82ba8b4bffcf96baafe038268000000'))
	while i < len(bytestring) - 1:
		# print(f'i is {i}\n') # For debugging
		if bytestring[i].to_bytes() == b'\x96':
			messageString += callDict.get(int(bytestring[i + 1]))
			i += 2
		else:
			try:
				messageString += getRadioChar(bytestring[ i : i + 2 ].hex())
			except:
				print(f'Unable to translate Japanese byte code {bytestring[i : i + 2].hex()}!!!\n')
				messageString += '[?]'
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
"""
Use this to test all characters in a radio call
campbellDict = makeCallDictionary(bytes.fromhex('0a0b000eaba92dfffe3c0e00bc2c003c3ffc2cbae82ed2c02c42c02c6ae92cbffe0000003febfc3aebac3aebac3febfc3aaa6c3aeb6c3aff2c3aeb2c3aeb2c3bffac380bb80000000038002ffff02eaab02ffff02eaab02eaab02ffff02c2db42c0be06ef2e9bea06c0000000e0aa80e0ffc3fe0282ee0b42de0e03aeffe3adae91f80e00bd0e07ea6e02413d000000028bffc1ebaac25b02c78b02c1dbffc006ee80a2ce00e38e02db4e97ae0ee2580bd000000003800003800003800003800003ff0003aa00038000038000038006abaa9bffffe000000002c00002c003ffffc3aaeac382c2c382c2c3ffffc3aaeac242c18002c00002c00000000002c00002c000ffff00eaeb00e2cb06eaeb9bffffe00be0006eb906f81f92900680000002ffff82eaab82ffff82eaab82ffff81ab4900fe8e06aeae9bffffe1bc0e00e40e0000000bf9ea4bbbeb8b757a0ba6ff9ba3aacb76ae8b3aee8b7aee9bbbffeb502c0b002c00000000fffe00aabd000ab40007d00bffffe6abaad00387800382400380002b80002f40000000026fff879baf429afe802ebac6afffcbeebac2eebac2e8b7c2e4624bbfffd20aaa8000000002c002c2c382c2c382eaeb82ffff8002c00382c2c382c2c3aaeac3ffffc38002c0000000d0e006c2ffcbabeb83f5bb42e4be47eaebdbeeaa82a6ffc7bac2caaeffc5eaeac0000002ffffc2eaeac2effec2daeac2effec2daaac2effec3aeaec3affecb5aaec2000b80000001d02c00bbffe22baee78b2c91dbffc00bbac0abb280eb7b42da2e078ebf9246e2c0000002396806bb6c0bffbfe2efbad77abac0746a8bffaf86eb4f07da2f86febad39ba480000002c3ffc2c3aac2c3ffcbf3aac6e2aa82cbffe2c2ea92fbaeebe2edea42aee00077800000000280000be0002d7801b41e47effbd11aa440aaaa00ffff00e00b00ffff00eaab00000000038003ffffc2aeba86aeba9bffffe0aaaa00ffff00eaab00eaab00ffff00eaab0000000002ba8bfbaacbbbffcb3baacb3baa8b3bffeb3baa9bbbffebfa59eb07aee00baed0000003ffffc2baae80baae00bffe00b00e00bffe00baae00b00e96bfffebeaae00000e0000000002c00002c00002c00052c500b2ce01e2cb42c2c38782c2d102c0401ac0000f8000000000ffff00eaab00ebff06ebab9baaaaebbffee0baae00baae00bffe00b06e00b03d00000006aaea9bffffe26aea03bfff03baab03baab03bfff03baab03aaaa03ffffe3aaaa90000000e3ffe0e3aa9bfbaa86e7bfc0e38000fbffebe7bb96e3bba0e77b86eb7ed3d2b880000007728ec3bb8ee2ab8e93ffffe3baee83baced3ffcf82ba8b4bffcf96baafe038268000000'))
for x in range(len(campbellDict)):
	print(f'{campbellDict.get(x)}')

"""
translatedText = translateJapaneseHex(bytes.fromhex('8144 812f 814a d002 906a 9606 8138 812e 824b d006 8228 812f 9607 9608 812e 9609 960a 906e 5c72 5c6e 8120 8111 8149 8117 8104 d003 00'))
print(translatedText)


