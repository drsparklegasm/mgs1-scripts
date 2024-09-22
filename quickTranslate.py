from radioTools import radioDict as RD

text = "9C 15 9C 16 81 2E 82 17 C2 43 D0 06 82 3E 82 53 20 82 30 82 4B 82 0B 82 53 C0 7F 82 4C 82 04 82 36 82 53 00"
textToPrint = RD.translateJapaneseHex(bytes.fromhex(text), callDict = {} )
print(textToPrint)

# FOX HOUND 部隊と彼等の率いる次世代特殊部隊が