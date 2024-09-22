from radioTools import radioDict as RD

text = "80 23 80 7B 46 4F 58 20 48 4F 55 4E 44 D0 02 82 35 C2 09 C2 23 82 0F 82 19 82 2F 82 06 82 53 82 29 C0 7D 80 23 9C 0A 9C 0B 81 28 80 7C 9C 0C 9C 0D 81 2E 9C 0E 81 04 81 4B 9C 0F 9C 10 9C 11 9C 12 9C 13 9C 0A 9C 0B 81 0C"
textToPrint = RD.translateJapaneseHex(bytes.fromhex(text), callDict = {} )
print(textToPrint)

# FOX HOUND 部隊と彼等の率いる次世代特殊部隊が