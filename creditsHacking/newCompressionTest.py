import os, struct
from PIL import Image
import numpy as np
# from creditsHacking.creditsHacking import imageData
import argparse

debug = True

def compressLine(data: bytes) -> bytes:

    global debug

    def findNextPatternOrRepeat(data: bytes, index: int) -> int:
        """
        Finds how many bytes starting at index
        until either we repeat the same byte 4x 
        or the next 4 bytes are a repeated pattern
        """
        count = 0
        checkLength = 3
        while True:
            patternCheck = data[index + count: index + count + checkLength]
            if len(set(patternCheck)) == 1 or data[:index + count].find(patternCheck) != -1:
                break
            else:
                count += 1
        
        return count

    def getLongestRepeat(data: bytes, index: int) -> int:
        """
        Get the longest repeated character starting at index.
        """

        before = data[:index]
        after = data[index:]

        count = 0
        while count < min(128, len(after)):
            if len(set(after[:count + 1])) == 1:
                count += 1
            else:
                break

        # print(f'{count} bytes were repeated following index {index}' )
        return count

    def getLongestPattern(data: bytes, index: int) -> tuple [int, int]:
        """
        For the index, return the longest pattern starting there that 
        appears earlier in the data and how far back to go.
        """
        before = data[:index]
        after = data[index:]

        count = 0
        while count < len(after):
            if before.find(after[:count + 1]) != -1:
                count += 1
            else:
                break
        
        distance = abs(len(before) - before.rfind(after[:count]))

        return distance, count
    
    """
    Actual compression Def starts here.

    """
    
    compressedData = b''
    i = 0

    while i < len(data):
        newBytes = b''
        repeatCount = getLongestRepeat(data, i)
        distance, patternLen = getLongestPattern(data, i)

        if patternLen >= repeatCount and patternLen > 1:
            if data[i - 1] == data[i]:
                newBytes += (repeatCount + 0x80).to_bytes() + int(1).to_bytes()
                i += repeatCount
            else:
                newBytes += (patternLen + 0x80).to_bytes() + distance.to_bytes()
                i += patternLen
        elif repeatCount > 3:
            if data[i - 1] == data[i] and i != 0: 
                newBytes += (repeatCount + 0x80).to_bytes() + int(1).to_bytes()
                i += repeatCount
            else:
                newBytes += int(1).to_bytes() + data[i].to_bytes()
                newBytes += (repeatCount - 1 + 0x80).to_bytes() + int(1).to_bytes()
                i += repeatCount
        else:
            newString = findNextPatternOrRepeat(data, i)
            if newString < 1:
                newString = 1
            newBytes += newString.to_bytes() + data[i : i + newString]
            i += newString
        if debug: 
            print(f'Compressed data: {newBytes.hex(sep=' ')}')
        
        compressedData += newBytes
    
    compressedData += bytes.fromhex('00')
    
    return compressedData


line = bytes.fromhex('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')

print(compressLine(line).hex(sep=' '))

"""
ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
6f 40 f2 0b 04 fb 04 aa ba ff bf 60 ff ef 41 0d f5 6f b0
ffffffff
04fdeeff9f50abebff143ef3cf60ef04fcffff0483fdbf50ffdf505fc0ffff09f905fcef31ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff

"""
# Original
# 01 FF B1 01 13 6F 40 F2 0B 04 FB 04 AA BA FF BF 60 FF EF 41 0D F5 6F B0 84 17 11 04 FD EE FF 9F 50 AB EB FF 14 3E F3 CF 60 EF 04 FC 83 13 11 83 FD BF 50 FF DF 50 5F C0 FF FF 09 F9 05 FC EF 31 B2 6E 00
# 01 ff b1 01 13 6f 40 f2 0b 04 fb 04 aa ba ff bf 60 ff ef 41 0d f5 6f b0 84 17 81 11 10 fd ee ff 9f 50 ab eb ff 14 3e f3 cf 60 ef 04 fc 83 13 11 83 fd bf 50 ff df 50 5f c0 ff ff 09 f9 05 fc ef 31 b2 6e 00
# mine