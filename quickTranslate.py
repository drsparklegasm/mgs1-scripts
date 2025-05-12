import translation.radioDict as RD

text = ""
textToPrint = RD.translateJapaneseHex(bytes.fromhex(text), callDict = {} )
print(textToPrint)
