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