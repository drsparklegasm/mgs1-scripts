from PIL import Image
import numpy as np

def getColors(palette: bytes) -> list:
    """
    Returns a list of colors in the palette.
    Each color is a Tuple (r, g, b) of 0 <= 255
    """
    # Quick def for getting the RGB values
    def getRGBfromHex(colorBytes: bytes) -> tuple [int, int, int]:
        """
        Calculates the color from the 2-byte color in the palette.
        """
        # Swap the two bytes for little-endian (since color is coming in as a 16-bit integer)
        color = int.from_bytes(colorBytes, byteorder='big')
        color = (color >> 8) | ((color & 0xFF) << 8)

        # Mask out the first bit (16th bit, which is always 0)
        color &= 0x7FFF  # 0x7FFF masks the first bit, leaving 15 bits

        # Extract the 5 bits for Red, Green, and Blue
        r = (color >> 10) & 0x1F  # Red: bits 10-14
        g = (color >> 5) & 0x1F   # Green: bits 5-9
        b = color & 0x1F          # Blue: bits 0-4

        # Normalize the 5-bit values to 8-bit (0-255) range
        r_normalized = int((r / 31) * 255)
        g_normalized = int((g / 31) * 255)
        b_normalized = int((b / 31) * 255)
        # print(f'{colorBytes.hex()} {r_normalized}')

        # Return normalized 8-bit values for red, green, and blue
        return (r_normalized, g_normalized, b_normalized)
    
    rgbColors = []
    i = 0
    while i < len(palette):
        rgbColors.append(getRGBfromHex(palette[i: i + 2]))
        i += 2
    
    return rgbColors

"""i = 0
while i < 32:
    number = int((i / 31) * 255)
    print(number, end=' ')
    i += 1
print()

i = 0
while i < 32:
    number = int(((i + 1) / 32) * 255)
    print(number, end=' ')
    i += 1"""

originalBytes =     b'73 4E 52 4A 31 46 10 42 CE 39 AD 35 8C 31 4A 29 29 25 E7 1C A5 14 84 10 63 0C 42 08 21 04 00 00'
NewLogic =          b'73 4e 52 4a 31 46 10 42 ce 39 ad 35 8c 31 4a 29 29 25 e7 1c a5 14 84 10 63 0c 42 08 21 04 00 00'
myBytes =           b'52 4a 31 46 10 42 ef 3d ad 35 8c 31 6b 2d 29 25 08 21 c6 18 84 10 63 0c 42 08 21 04 00 00 00 00'

print(getColors(originalBytes))
print(getColors(myBytes))

"""
'73 4E 52 4A 31 46 10 42 CE 39 AD 35 8C 31 4A 29 29 25 E7 1C A5 14 
84 10 63 0C 42 08 21 04 00 00'
'52 4a 31 46 10 42 ef 3d ad 35 8c 31 6b 2d 29 25 08 21 c6 18 
84 10 63 0c 42 08 21 04 00 00'





From original:

734e (156, 156, 156)
524a (148, 148, 148)
3146 (139, 139, 139)
1042 (131, 131, 131)
ce39 (115, 115, 115)
ad35 (106, 106, 106)
8c31 (98, 98, 98)
4a29 (82, 82, 82)
2925 (74, 74, 74)
e71c (57, 57, 57)
a514 (41, 41, 41)
8410 (32, 32, 32)
630c (24, 24, 24)
4208 (16, 16, 16)
2104 (8, 8, 8)
0000 (0, 0, 0)

New logic (* 32)

(0, 0, 0), 0000
(8, 8, 8), 0421
(16, 16, 16), 0842
(24, 24, 24), 0c63
(32, 32, 32), 1084
(41, 41, 41), 14a5
(57, 57, 57), 1ce7
(74, 74, 74), 2529
(82, 82, 82), 294a
(98, 98, 98), 318c
(106, 106, 106), 35ad
(115, 115, 115), 39ce
(131, 131, 131), 4210
(139, 139, 139), 4631
(148, 148, 148), 4a52
(156, 156, 156), 4e73




"""

# testData from first image:

testDataA = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
# Bytes should be 01 FF / FF 01 / A0 01 / 00
# My bytes: 02 ff ff 82 9e 00
testDataB = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f21fe9f11fb14000059000110fe3e60ff8fb2ffffffffcf0300d49f010040ff5f40ffcf0100b3ffffff3c0092ff6f0030fb6fd2ffff19f9150051fdffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
"""
Command: 01 - Adding 1 bytes: "ff" 
Command: b1 Position: -1 - > 0x80: Repeating: Added 49 bytes. Wrote ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 
Command: 13 - Adding 19 bytes: "7f21fe9f11fb14000059000110fe3e60ff8fb2" 
Command: 84 Position: -23 - > 0x80: Repeating: Added 4 bytes. Wrote ffffffff 
Command: 10 - Adding 16 bytes: "cf0300d49f010040ff5f40ffcf0100b3" 
Command: 83 Position: -19 - > 0x80: Repeating: Added 3 bytes. Wrote ffffff 
Command: 12 - Adding 18 bytes: "3c0092ff6f0030fb6fd2ffff19f9150051fd" 
Command: b2 Position: -110 - > 0x80: Repeating: Added 50 bytes. Wrote ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 
Command: 00 - ENDING LINE 
"""
## 01 FF B1 01 13 7F 21 FE 9F 11 FB 14 00 00 59 00 01 10 FE 3E 60 FF 8F B2 84 17 10 CF 03 00 D4 9F 01 00 40 FF 5F 40 FF CF 01 00 B3 83 13 12 3C 00 92 FF 6F 00 30 FB 6F D2 FF FF 19 F9 15 00 51 FD B2 6E 00
testDataC = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6f00f95f00fb049999bd6940a9ff0a21ff6fb0ffffffff2e708b709f509ab9ff1d01fccf408a12fdffff23ba33ff07b419e25fc0ffff09f9057604e3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
# 01 FF B1 01 13 6F 00 F9 5F 00 FB 04 99 99 BD 69 40 A9 FF 0A 21 FF 6F B0 84 17 25 2E 70 8B 70 9F 50 9A B9 FF 1D 01 FC CF 40 8A 12 FD FF FF 23 BA 33 FF 07 B4 19 E2 5F C0 FF FF 09 F9 05 76 04 E3 B2 6E 00 
# 


# ORIGINAL IMAGE DATA: 00b8ba.rar

# 00
# 01 FF FF 01 A0 01 00
# 01 FF FF 01 A0 01 00
# 01 FF FF 01 A0 01 00
# 01 FF B1 01 13 7F 21 FE 9F 11 FB 14 00 00 59 00 01 10 FE 3E 60 FF 8F B2 84 17 10 CF 03 00 D4 9F 01 00 40 FF 5F 40 FF CF 01 00 B3 83 13 12 3C 00 92 FF 6F 00 30 FB 6F D2 FF FF 19 F9 15 00 51 FD B2 6E 00
# 01 FF B1 01 13 6F 00 F9 5F 00 FB 04 99 99 BD 69 40 A9 FF 0A 21 FF 6F B0 84 17 25 2E 70 8B 70 9F 50 9A B9 FF 1D 01 FC CF 40 8A 12 FD FF FF 23 BA 33 FF 07 B4 19 E2 5F C0 FF FF 09 F9 05 76 04 E3 B2 6E 00
# 01 FF B1 01 07 6F 11 F5 2E 13 FB 04 83 0A 09 BF 70 FF FF 15 05 FB 6F B0 84 17 06 08 F7 FF EB 9F A0 84 09 1A 06 F6 CF 70 FF 06 FB FF EF 40 FF DE FF 22 FE 8F 80 5F C0 FF FF 09 F9 05 FD 7F 83 30 B0 01 00
# 01 FF B1 01 13 6F 40 F2 0B 04 FB 04 AA BA FF BF 60 FF EF 41 0D F5 6F B0 84 17 11 04 FD EE FF 9F 50 AB EB FF 14 3E F3 CF 60 EF 04 FC 83 13 11 83 FD BF 50 FF DF 50 5F C0 FF FF 09 F9 05 FC EF 31 B2 6E 00
# 01 FF B1 01 13 6F 81 C0 17 07 FB 04 00 40 FF BF 60 FF 9F 90 3F F2 6F B0 84 17 10 04 FF 04 31 9F 00 01 C1 DF 50 6F B0 CF 10 23 60 83 13 12 6E 01 81 BF 70 FF FF 40 5F C0 FF FF 09 F9 05 FC FF 33 B2 6E 00
# 01 FF B1 01 13 6F C0 60 44 09 FB 04 CB DC FF BF 60 FF 4F 30 14 A0 6F B0 84 17 10 04 FD 8A 23 9F 60 CC FC 8F 20 24 60 CF 40 28 F3 84 14 11 9E 02 CC 50 FF DF 50 5F C0 FF FF 09 F9 05 FC EF 31 B2 6E 00
# 01 FF B1 01 07 6F F0 34 91 0A FB 04 83 0A 09 BF 60 FF 1E 53 44 50 7F B0 84 17 25 08 F8 FF 25 9F A0 FF FF 4F 41 54 32 CF 70 9F 80 FF FF DF C5 FF 08 F9 22 FF 8F 80 5F D0 FF FF 09 F9 05 FD 7F 70 B2 6E 00
# 01 FF B1 01 3C 6F F0 07 D0 09 FB 04 99 99 FC BF 60 FF 09 F9 FF 13 7F 50 77 D7 FF FF 2E 91 AD 32 9F 50 9A B9 0C F5 FF 06 DB 60 FF 13 FE FF CF 30 BA 04 FB 07 B4 19 E2 5F 60 77 E8 09 F9 05 76 04 E3 B2 6E 00
# 01 FF B1 01 3C 7F F1 1C F3 19 FB 14 00 00 F7 BF 82 FF 14 FE FF 09 8B 01 00 B0 FF FF CF 03 01 B3 9F 01 00 30 17 FB FF 1C D7 71 FF 08 F6 FF FF 2A 00 70 FF 6F 00 30 FB 5F 01 00 D0 1A F9 15 00 51 FD B2 6E 00
# 01 FF FF 01 A0 01 00
# 01 FF FF 01 A0 01 00
# 01 FF FF 01 A0 01 00
# 01 FF FF 01 A0 01 00



# 01 ff b1 01 07 6f 11 f5 2e 13 fb 04 0c ff ff ff bf 70 ff ff 15 05 fb 6f b0 84 17 06 08 f7 ff eb 9f a0 84 09 1b 06 f6 cf 70 ff 06 fb ff ef 40 ff de ff 22 fe 8f 80 5f c0 ff ff 09 f9 05 fd 7f 70 b2 6e 00
#  MY lines:

# 01 ff ff 01 a0 01 00
# 01 ff ff 01 a0 01 00
# 01 ff ff 01 a0 01 00
# 01 ff ff 01 a0 01 00
# 01 ff ff 01 a0 01 00
# 01 ff b1 01 13 7f 21 fe 9f 11 fb 14 00 00 59 00 01 10 fe 3e 60 ff 8f b2 84 17 10 cf 03 00 d4 9f 01 00 40 ff 5f 40 ff cf 01 00 b3 83 13 12 3c 00 92 ff 6f 00 30 fb 6f d2 ff ff 19 f9 15 00 51 fd b2 6e 00
# 01 ff b1 01 13 6f 00 f9 5f 00 fb 04 99 99 bd 69 40 a9 ff 0a 21 ff 6f b0 84 17 25 2e 70 8b 70 9f 50 9a b9 ff 1d 01 fc cf 40 8a 12 fd ff ff 23 ba 33 ff 07 b4 19 e2 5f c0 ff ff 09 f9 05 76 04 e3 b2 6e 00
# 01 ff b1 01 07 6f 11 f5 2e 13 fb 04 83 0a 09 bf 70 ff ff 15 05 fb 6f b0 84 17 06 08 f7 ff eb 9f a0 83 09 1c 08 06 f6 cf 70 ff 06 fb ff ef 40 ff de ff 22 fe 8f 80 5f c0 ff ff 09 f9 05 fd 7f 70 b2 6e 00 # This is the line not compressing correctly.
# 01 ff b1 01 13 6f 40 f2 0b 04 fb 04 aa ba ff bf 60 ff ef 41 0d f5 6f b0 84 17 25 04 fd ee ff 9f 50 ab eb ff 14 3e f3 cf 60 ef 04 fc ff ff 04 83 fd bf 50 ff df 50 5f c0 ff ff 09 f9 05 fc ef 31 b2 6e 00
# 01 ff b1 01 13 6f 81 c0 17 07 fb 04 00 40 ff bf 60 ff 9f 90 3f f2 6f b0 84 17 10 04 ff 04 31 9f 00 01 c1 df 50 6f b0 cf 10 23 60 83 13 12 6e 01 81 bf 70 ff ff 40 5f c0 ff ff 09 f9 05 fc ff 33 b2 6e 00
# 01 ff b1 01 13 6f c0 60 44 09 fb 04 cb dc ff bf 60 ff 4f 30 14 a0 6f b0 84 17 10 04 fd 8a 23 9f 60 cc fc 8f 20 24 60 cf 40 28 f3 84 14 11 9e 02 cc 50 ff df 50 5f c0 ff ff 09 f9 05 fc ef 31 b2 6e 00
# 01 ff b1 01 07 6f f0 34 91 0a fb 04 83 0a 09 bf 60 ff 1e 53 44 50 7f b0 84 17 25 08 f8 ff 25 9f a0 ff ff 4f 41 54 32 cf 70 9f 80 ff ff df c5 ff 08 f9 22 ff 8f 80 5f d0 ff ff 09 f9 05 fd 7f 70 b2 6e 00
# 01 ff b1 01 3c 6f f0 07 d0 09 fb 04 99 99 fc bf 60 ff 09 f9 ff 13 7f 50 77 d7 ff ff 2e 91 ad 32 9f 50 9a b9 0c f5 ff 06 db 60 ff 13 fe ff cf 30 ba 04 fb 07 b4 19 e2 5f 60 77 e8 09 f9 05 76 04 e3 b2 6e 00
# 01 ff b1 01 3c 7f f1 1c f3 19 fb 14 00 00 f7 bf 82 ff 14 fe ff 09 8b 01 00 b0 ff ff cf 03 01 b3 9f 01 00 30 17 fb ff 1c d7 71 ff 08 f6 ff ff 2a 00 70 ff 6f 00 30 fb 5f 01 00 d0 1a f9 15 00 51 fd b2 6e 00
# 01 ff ff 01 a0 01 00
# 01 ff ff 01 a0 01 00
# 01 ff ff 01 a0 01 00
# 01 ff ff 01 a0 01 00