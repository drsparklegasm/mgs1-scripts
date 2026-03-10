"""
MGS1 Font Tools — Extract and inject 12x12 kana/kanji glyphs from STAGE.DIR

The font is embedded in the init stage of STAGE.DIR. It contains:
  - 12-byte header
  - 384-byte ASCII VFW table (96 entries x 4 bytes)
  - 1908-byte ASCII glyph data (variable width, 12px tall)
  - 3 null bytes
  - 15,840 bytes of kana/kanji glyph data (440 glyphs x 36 bytes each, fixed 12x12 2bpp)

This module handles the kana/kanji section only. Each glyph is 12x12 pixels at
2 bits per pixel (4 grayscale levels), packed 4 pixels per byte, MSB-first.
"""

import struct
from PIL import Image

# Font location within STAGE.DIR
FONT_ABS_OFFSET = 0x565DF8
FONT_TOTAL_SIZE = 18184
FONT_HEADER_SIGNATURE = b'\x00\x00\x01\x88'  # bytes 4-7 of the 12-byte header

# Layout within the font
HEADER_SIZE = 12
ASCII_VFW_SIZE = 384
ASCII_GLYPH_SIZE = 1908
NULL_PAD = 3
KANA_OFFSET = HEADER_SIZE + ASCII_VFW_SIZE + ASCII_GLYPH_SIZE + NULL_PAD  # 0x903

# Glyph constants
GLYPH_SIZE = 36       # bytes per glyph (12x12 at 2bpp)
GLYPH_WIDTH = 12
GLYPH_HEIGHT = 12
GLYPH_COUNT = 440     # total kana/kanji slots
KANA_DATA_SIZE = GLYPH_COUNT * GLYPH_SIZE  # 15840

# 2bpp grayscale palette: 2-bit value -> 8-bit grayscale
PALETTE = [0x00, 0x55, 0xAA, 0xFF]


def _verifyFontHeader(data: bytes) -> bool:
    """Check that the font header signature is present at the expected position."""
    return data[4:8] == FONT_HEADER_SIGNATURE


def extractFontBlock(stageDirPath: str) -> bytes:
    """Read the entire font block (18,184 bytes) from STAGE.DIR."""
    with open(stageDirPath, 'rb') as f:
        f.seek(FONT_ABS_OFFSET)
        data = f.read(FONT_TOTAL_SIZE)
    if len(data) < FONT_TOTAL_SIZE:
        raise ValueError(f"STAGE.DIR too small: expected {FONT_TOTAL_SIZE} bytes at offset 0x{FONT_ABS_OFFSET:X}")
    if not _verifyFontHeader(data):
        raise ValueError(f"Font header signature not found at offset 0x{FONT_ABS_OFFSET:X}. "
                         "Is this the correct STAGE.DIR?")
    return data


def extractGlyphs(stageDirPath: str) -> list[bytes]:
    """Extract all 440 kana/kanji glyphs from STAGE.DIR as 36-byte chunks."""
    fontData = extractFontBlock(stageDirPath)
    glyphs = []
    for i in range(GLYPH_COUNT):
        start = KANA_OFFSET + i * GLYPH_SIZE
        glyphs.append(fontData[start:start + GLYPH_SIZE])
    return glyphs


def glyphToPixels(data: bytes) -> list[list[int]]:
    """Convert 36-byte 2bpp glyph to 12x12 pixel array (values 0-3)."""
    if len(data) != GLYPH_SIZE:
        raise ValueError(f"Expected {GLYPH_SIZE} bytes, got {len(data)}")
    pixels = []
    byteIdx = 0
    for _row in range(GLYPH_HEIGHT):
        row = []
        for _col in range(0, GLYPH_WIDTH, 4):  # 4 pixels per byte
            b = data[byteIdx]
            row.append((b >> 6) & 0x03)
            row.append((b >> 4) & 0x03)
            row.append((b >> 2) & 0x03)
            row.append(b & 0x03)
            byteIdx += 1
        pixels.append(row)
    return pixels


def pixelsToGlyph(pixels: list[list[int]]) -> bytes:
    """Convert 12x12 pixel array (values 0-3) back to 36-byte 2bpp glyph."""
    result = bytearray()
    for row in pixels:
        for col in range(0, GLYPH_WIDTH, 4):
            b = ((row[col] & 0x03) << 6 |
                 (row[col+1] & 0x03) << 4 |
                 (row[col+2] & 0x03) << 2 |
                 (row[col+3] & 0x03))
            result.append(b)
    return bytes(result)


def glyphToImage(data: bytes) -> Image.Image:
    """Convert a 36-byte glyph to a PIL Image (12x12 grayscale)."""
    pixels = glyphToPixels(data)
    img = Image.new('L', (GLYPH_WIDTH, GLYPH_HEIGHT))
    for y, row in enumerate(pixels):
        for x, val in enumerate(row):
            img.putpixel((x, y), PALETTE[val])
    return img


def imageToGlyph(image: Image.Image) -> bytes:
    """Convert a PIL Image to a 36-byte 2bpp glyph. Image is scaled to 12x12 and quantized."""
    img = image.convert('L').resize((GLYPH_WIDTH, GLYPH_HEIGHT), Image.NEAREST)
    pixels = []
    for y in range(GLYPH_HEIGHT):
        row = []
        for x in range(GLYPH_WIDTH):
            gray = img.getpixel((x, y))
            # Quantize to nearest 2bpp level
            best = min(range(4), key=lambda i: abs(PALETTE[i] - gray))
            row.append(best)
        pixels.append(row)
    return pixelsToGlyph(pixels)


def glyphToPng(data: bytes, path: str) -> None:
    """Save a single glyph as a PNG file."""
    img = glyphToImage(data)
    img.save(path)


def pngToGlyph(path: str) -> bytes:
    """Load a PNG file and convert to a 36-byte 2bpp glyph."""
    img = Image.open(path)
    return imageToGlyph(img)


def exportAllGlyphs(stageDirPath: str, outputDir: str) -> None:
    """Extract all 440 glyphs and save as individual PNGs."""
    import os
    os.makedirs(outputDir, exist_ok=True)
    glyphs = extractGlyphs(stageDirPath)
    for i, glyph in enumerate(glyphs):
        path = os.path.join(outputDir, f'glyph-{i:03d}.png')
        glyphToPng(glyph, path)


def importGlyphsFromFolder(folder: str) -> dict[int, bytes]:
    """Scan folder for glyph-NNN.png files, return dict of slot index -> 36-byte glyph data."""
    import os, re
    result = {}
    pattern = re.compile(r'^glyph-(\d{3})\.png$')
    for name in os.listdir(folder):
        m = pattern.match(name)
        if m:
            idx = int(m.group(1))
            if 0 <= idx < GLYPH_COUNT:
                result[idx] = pngToGlyph(os.path.join(folder, name))
    return result


def injectGlyphs(stageDirPath: str, outputPath: str, glyphs: list[bytes]) -> None:
    """Patch kana/kanji glyphs into STAGE.DIR and write to outputPath.

    glyphs: list of 440 x 36-byte chunks. Use extractGlyphs() to get the
    originals, modify slots as needed, then pass the full list here.
    """
    if len(glyphs) != GLYPH_COUNT:
        raise ValueError(f"Expected {GLYPH_COUNT} glyphs, got {len(glyphs)}")
    for i, g in enumerate(glyphs):
        if len(g) != GLYPH_SIZE:
            raise ValueError(f"Glyph {i} is {len(g)} bytes, expected {GLYPH_SIZE}")

    with open(stageDirPath, 'rb') as f:
        data = bytearray(f.read())

    # Verify we're patching the right location
    headerSlice = data[FONT_ABS_OFFSET:FONT_ABS_OFFSET + HEADER_SIZE]
    if headerSlice[4:8] != FONT_HEADER_SIGNATURE:
        raise ValueError("Font header signature not found. Is this the correct STAGE.DIR?")

    # Patch the kana/kanji region
    kanaStart = FONT_ABS_OFFSET + KANA_OFFSET
    for i, glyph in enumerate(glyphs):
        offset = kanaStart + i * GLYPH_SIZE
        data[offset:offset + GLYPH_SIZE] = glyph

    with open(outputPath, 'wb') as f:
        f.write(data)
