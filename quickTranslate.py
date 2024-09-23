import radioTools.radioDict as RD

text = ""
textToPrint = RD.translateJapaneseHex(bytes.fromhex(text), callDict = {} )
print(textToPrint)
