"""
MGS1 Font Tools — Extract, parse, and rebuild the init-stage font from STAGE.DIR

The font is located by scanning for its header signature rather than using a
hardcoded offset, so this works across different game versions (JPN, US, PAL, etc.).

Font layout (all sizes derived from the 12-byte header pointers):
  - 12-byte header
  - 384-byte ASCII VFW table (96 entries x 4 bytes)
  - Variable-size ASCII glyph data (96 chars, variable width, 12px tall, 2bpp)
  - 3 null bytes (padding)
  - Kana/kanji glyph data (N glyphs x 36 bytes each, fixed 12x12 2bpp)

All glyph data uses 2-bit-per-pixel encoding, packed continuously (no row
padding), MSB-first: bits 7-6 = pixel 0, 5-4 = pixel 1, 3-2 = pixel 2, 1-0 = pixel 3.
"""

import struct
from PIL import Image

# ── Constants ────────────────────────────────────────────────────────────────

FONT_HEADER_SIGNATURE = b'\x00\x00\x01\x88'  # bytes 4-7 of the 12-byte header
HEADER_SIZE = 12
VFW_ENTRY_SIZE = 4
ASCII_CHAR_COUNT = 96
ASCII_VFW_SIZE = ASCII_CHAR_COUNT * VFW_ENTRY_SIZE  # 384
GLYPH_HEIGHT = 12           # all glyphs are 12px tall
KANA_GLYPH_WIDTH = 12       # kana/kanji are fixed 12px wide
KANA_GLYPH_SIZE = 36        # 12x12 at 2bpp = 36 bytes
NULL_PAD = 3

# 2bpp grayscale palette: 2-bit value -> 8-bit grayscale
PALETTE = [0x00, 0x55, 0xAA, 0xFF]


# ── FontBlock: parsed font data ─────────────────────────────────────────────

class FontBlock:
    """Holds all parsed data from a STAGE.DIR font block."""

    def __init__(self):
        self.fileOffset: int = 0       # absolute byte offset within STAGE.DIR
        self.totalSize: int = 0        # total font block size in bytes

        # ASCII section (96 variable-width characters)
        self.asciiVfwBytes: list[int] = []  # raw first byte of each VFW entry (width + flags)
        self.asciiGlyphs: list[bytes] = []  # raw 2bpp glyph data per character

        # Kana/kanji section (N fixed 12x12 characters)
        self.kanaGlyphs: list[bytes] = []   # 36-byte chunks
        self._trailingBytes: bytes = b''    # trailing pad bytes after kana data

    @property
    def kanaCount(self) -> int:
        return len(self.kanaGlyphs)

    @property
    def asciiCount(self) -> int:
        return len(self.asciiGlyphs)

    def asciiPixelWidth(self, idx: int) -> int:
        """Derive actual pixel width from glyph data size.

        width * GLYPH_HEIGHT / 4 = len(data), since 2bpp packs 4 pixels/byte.
        So width = len(data) * 4 / GLYPH_HEIGHT = len(data) / 3.
        """
        if idx < 0 or idx >= len(self.asciiGlyphs):
            return 0
        return len(self.asciiGlyphs[idx]) // 3


# ── Signature scanning ──────────────────────────────────────────────────────

def findFontOffset(data: bytes) -> int:
    """Scan raw STAGE.DIR bytes for the font header signature.

    Returns the absolute byte offset of the font block start, or raises
    ValueError if no valid font header is found.
    """
    searchFrom = 0
    while True:
        pos = data.find(FONT_HEADER_SIGNATURE, searchFrom)
        if pos < 0:
            raise ValueError(
                "Font header signature not found in file. "
                "Is this a valid STAGE.DIR?")

        # Signature sits at bytes 4-7, so the header starts 4 bytes earlier
        headerStart = pos - 4
        if headerStart < 0:
            searchFrom = pos + 1
            continue

        if headerStart + HEADER_SIZE > len(data):
            searchFrom = pos + 1
            continue

        header = data[headerStart:headerStart + HEADER_SIZE]
        pointer1 = struct.unpack_from('<I', header, 0)[0]  # total size - 4
        pointer2 = struct.unpack_from('>I', header, 8)[0]  # header+VFW+ASCII - 1

        totalSize = pointer1 + 4
        asciiEnd = pointer2 + 1  # offset within font where null pad starts

        # Sanity: ASCII glyph data must exist
        asciiGlyphSize = asciiEnd - HEADER_SIZE - ASCII_VFW_SIZE
        if asciiGlyphSize <= 0:
            searchFrom = pos + 1
            continue

        # Sanity: kana section must fit at least one 36-byte glyph
        kanaDataSize = totalSize - asciiEnd - NULL_PAD
        if kanaDataSize < KANA_GLYPH_SIZE:
            searchFrom = pos + 1
            continue

        # Ensure we can read the full block
        if headerStart + totalSize > len(data):
            searchFrom = pos + 1
            continue

        # Verify the 3 null-pad bytes between ASCII and kana sections
        padOffset = headerStart + asciiEnd
        if data[padOffset:padOffset + NULL_PAD] != b'\x00' * NULL_PAD:
            searchFrom = pos + 1
            continue

        return headerStart

    raise ValueError("Font header signature not found in file.")


# ── Font block parsing ──────────────────────────────────────────────────────

def parseFontBlock(data: bytes, fileOffset: int) -> FontBlock:
    """Parse a font block from raw STAGE.DIR data at the given offset.

    Derives all section sizes from the header pointers — no hardcoded sizes
    except the structural constants (header=12, VFW entry=4, kana glyph=36).
    """
    header = data[fileOffset:fileOffset + HEADER_SIZE]
    if header[4:8] != FONT_HEADER_SIGNATURE:
        raise ValueError(f"Font signature mismatch at offset 0x{fileOffset:X}")

    pointer1 = struct.unpack_from('<I', header, 0)[0]
    pointer2 = struct.unpack_from('>I', header, 8)[0]

    fb = FontBlock()
    fb.fileOffset = fileOffset
    fb.totalSize = pointer1 + 4

    asciiEnd = pointer2 + 1
    asciiGlyphDataSize = asciiEnd - HEADER_SIZE - ASCII_VFW_SIZE
    kanaDataSize = fb.totalSize - asciiEnd - NULL_PAD

    # ── Parse VFW table ──────────────────────────────────────────────────
    vfwStart = fileOffset + HEADER_SIZE
    offsets = []
    for i in range(ASCII_CHAR_COUNT):
        entryOff = vfwStart + i * VFW_ENTRY_SIZE
        vfwByte = data[entryOff]
        glyphOffset = int.from_bytes(data[entryOff + 1:entryOff + 4], 'big')
        fb.asciiVfwBytes.append(vfwByte)
        offsets.append(glyphOffset)

    # ── Extract ASCII glyphs ─────────────────────────────────────────────
    asciiDataStart = fileOffset + HEADER_SIZE + ASCII_VFW_SIZE
    for i in range(ASCII_CHAR_COUNT):
        start = offsets[i]
        if i + 1 < ASCII_CHAR_COUNT:
            end = offsets[i + 1]
        else:
            end = asciiGlyphDataSize
        fb.asciiGlyphs.append(data[asciiDataStart + start:asciiDataStart + end])

    # ── Extract kana/kanji glyphs ────────────────────────────────────────
    kanaStart = fileOffset + asciiEnd + NULL_PAD
    kanaCount = kanaDataSize // KANA_GLYPH_SIZE
    for i in range(kanaCount):
        start = kanaStart + i * KANA_GLYPH_SIZE
        fb.kanaGlyphs.append(data[start:start + KANA_GLYPH_SIZE])

    # Preserve any trailing bytes after the last complete glyph
    trailingStart = kanaStart + kanaCount * KANA_GLYPH_SIZE
    trailingEnd = fileOffset + fb.totalSize
    fb._trailingBytes = data[trailingStart:trailingEnd]

    return fb


def loadFont(stageDirPath: str) -> FontBlock:
    """Load and parse the font from a STAGE.DIR file."""
    with open(stageDirPath, 'rb') as f:
        data = f.read()
    offset = findFontOffset(data)
    return parseFontBlock(data, offset)


# ── Pixel encoding/decoding ─────────────────────────────────────────────────

def glyphToPixels(data: bytes, width: int = KANA_GLYPH_WIDTH,
                  height: int = GLYPH_HEIGHT) -> list[list[int]]:
    """Decode 2bpp packed glyph bytes into a 2D pixel array (values 0-3).

    Pixels are packed continuously (no row padding), 4 per byte, MSB-first.
    Works for both fixed-width kana (12x12) and variable-width ASCII glyphs.
    """
    allPixels = []
    for byte in data:
        allPixels.append((byte >> 6) & 3)
        allPixels.append((byte >> 4) & 3)
        allPixels.append((byte >> 2) & 3)
        allPixels.append(byte & 3)

    rows = []
    for r in range(height):
        start = r * width
        rows.append(allPixels[start:start + width])
    return rows


def pixelsToGlyph(pixels: list[list[int]]) -> bytes:
    """Encode a 2D pixel array (values 0-3) to 2bpp packed bytes.

    Packs continuously — the width is inferred from the row lengths.
    """
    flat = [p for row in pixels for p in row]
    # Pad to multiple of 4
    while len(flat) % 4:
        flat.append(0)
    result = bytearray()
    for i in range(0, len(flat), 4):
        b = ((flat[i] & 3) << 6 |
             (flat[i+1] & 3) << 4 |
             (flat[i+2] & 3) << 2 |
             (flat[i+3] & 3))
        result.append(b)
    return bytes(result)


# ── Image conversion ─────────────────────────────────────────────────────────

def glyphToImage(data: bytes, width: int = KANA_GLYPH_WIDTH,
                 height: int = GLYPH_HEIGHT) -> Image.Image:
    """Convert glyph bytes to a PIL grayscale image."""
    pixels = glyphToPixels(data, width, height)
    img = Image.new('L', (width, height))
    for y, row in enumerate(pixels):
        for x, val in enumerate(row):
            img.putpixel((x, y), PALETTE[val])
    return img


def imageToGlyph(image: Image.Image, width: int = KANA_GLYPH_WIDTH,
                 height: int = GLYPH_HEIGHT) -> bytes:
    """Convert a PIL image to 2bpp glyph bytes. Scales and quantizes as needed."""
    img = image.convert('L').resize((width, height), Image.NEAREST)
    pixels = []
    for y in range(height):
        row = []
        for x in range(width):
            gray = img.getpixel((x, y))
            best = min(range(4), key=lambda i: abs(PALETTE[i] - gray))
            row.append(best)
        pixels.append(row)
    return pixelsToGlyph(pixels)


def glyphToPng(data: bytes, path: str, width: int = KANA_GLYPH_WIDTH,
               height: int = GLYPH_HEIGHT) -> None:
    """Save a glyph as a PNG file."""
    glyphToImage(data, width, height).save(path)


def pngToGlyph(path: str, width: int = KANA_GLYPH_WIDTH,
               height: int = GLYPH_HEIGHT) -> bytes:
    """Load a PNG and convert to 2bpp glyph bytes."""
    return imageToGlyph(Image.open(path), width, height)


# ── Bulk export/import ───────────────────────────────────────────────────────

def exportAllGlyphs(stageDirPath: str, outputDir: str) -> None:
    """Export all glyphs (ASCII + kana) as PNGs."""
    import os
    os.makedirs(outputDir, exist_ok=True)
    fb = loadFont(stageDirPath)

    # ASCII glyphs: ascii-00.png through ascii-95.png
    for i, glyph in enumerate(fb.asciiGlyphs):
        w = fb.asciiPixelWidth(i)
        path = os.path.join(outputDir, f'ascii-{i:02d}.png')
        glyphToPng(glyph, path, w)

    # Kana glyphs: glyph-000.png through glyph-NNN.png
    for i, glyph in enumerate(fb.kanaGlyphs):
        path = os.path.join(outputDir, f'glyph-{i:03d}.png')
        glyphToPng(glyph, path)


def importKanaFromFolder(folder: str, kanaCount: int) -> dict[int, bytes]:
    """Scan folder for glyph-NNN.png files, return dict of slot -> 36-byte glyph."""
    import os, re
    result = {}
    pattern = re.compile(r'^glyph-(\d{3})\.png$')
    for name in os.listdir(folder):
        m = pattern.match(name)
        if m:
            idx = int(m.group(1))
            if 0 <= idx < kanaCount:
                result[idx] = pngToGlyph(os.path.join(folder, name))
    return result


def importAsciiFromFolder(folder: str) -> dict[int, bytes]:
    """Scan folder for ascii-NN.png files. Returns dict of index -> glyph_bytes.

    The image's own pixel width determines the glyph encoding width.
    """
    import os, re
    result = {}
    pattern = re.compile(r'^ascii-(\d{2})\.png$')
    for name in os.listdir(folder):
        m = pattern.match(name)
        if m:
            idx = int(m.group(1))
            if 0 <= idx < ASCII_CHAR_COUNT:
                img = Image.open(os.path.join(folder, name))
                w = img.width
                result[idx] = imageToGlyph(img, w)
    return result


# ── Font block recompilation ─────────────────────────────────────────────────

def buildFontBlock(fb: FontBlock) -> bytes:
    """Recompile a FontBlock into raw bytes suitable for injection into STAGE.DIR.

    Rebuilds header, VFW table, ASCII glyph data, null pad, and kana data
    from the current state of the FontBlock. All pointers are recomputed.
    """
    # ── ASCII glyph data: concatenate all 96 glyphs ──────────────────────
    asciiGlyphData = bytearray()
    offsets = []
    for glyph in fb.asciiGlyphs:
        offsets.append(len(asciiGlyphData))
        asciiGlyphData.extend(glyph)

    # ── VFW table ────────────────────────────────────────────────────────
    vfwData = bytearray()
    for i in range(ASCII_CHAR_COUNT):
        vfwData.append(fb.asciiVfwBytes[i] & 0xFF)
        vfwData.extend(offsets[i].to_bytes(3, 'big'))

    # ── Kana data ────────────────────────────────────────────────────────
    kanaData = bytearray()
    for glyph in fb.kanaGlyphs:
        kanaData.extend(glyph)

    # ── Trailing bytes (preserved from original) ────────────────────────
    trailing = fb._trailingBytes

    # ── Header ───────────────────────────────────────────────────────────
    asciiSectionEnd = HEADER_SIZE + ASCII_VFW_SIZE + len(asciiGlyphData)
    totalSize = asciiSectionEnd + NULL_PAD + len(kanaData) + len(trailing)

    pointer1 = totalSize - 4           # LE at offset 0
    pointer2 = asciiSectionEnd - 1     # BE at offset 8

    header = bytearray(HEADER_SIZE)
    struct.pack_into('<I', header, 0, pointer1)
    header[4:8] = FONT_HEADER_SIGNATURE
    struct.pack_into('>I', header, 8, pointer2)

    # ── Concatenate ──────────────────────────────────────────────────────
    result = bytearray()
    result.extend(header)
    result.extend(vfwData)
    result.extend(asciiGlyphData)
    result.extend(b'\x00' * NULL_PAD)
    result.extend(kanaData)
    result.extend(trailing)

    return bytes(result)


def injectFont(stageDirPath: str, outputPath: str, fb: FontBlock) -> None:
    """Rebuild the font block and patch it into STAGE.DIR at the original offset.

    Raises ValueError if the recompiled size differs from the original, since
    a size change would corrupt STAGE.DIR sector alignment.
    """
    with open(stageDirPath, 'rb') as f:
        data = bytearray(f.read())

    newBlock = buildFontBlock(fb)

    # Verify we're patching the right location
    if data[fb.fileOffset + 4:fb.fileOffset + 8] != FONT_HEADER_SIGNATURE:
        raise ValueError("Font signature not found at expected offset. Wrong file?")

    if len(newBlock) != fb.totalSize:
        raise ValueError(
            f"Recompiled font is {len(newBlock)} bytes but original was "
            f"{fb.totalSize}. Size changes would corrupt STAGE.DIR sector "
            f"alignment. Adjust ASCII glyph widths to match the original "
            f"total size.")

    data[fb.fileOffset:fb.fileOffset + len(newBlock)] = newBlock

    with open(outputPath, 'wb') as f:
        f.write(data)


# ── Backward-compatible convenience wrappers ─────────────────────────────────

# These constants are kept for external code that may reference them,
# but their values only apply to the JPN version. Use loadFont() instead.
GLYPH_SIZE = KANA_GLYPH_SIZE
GLYPH_WIDTH = KANA_GLYPH_WIDTH
GLYPH_COUNT = 440  # JPN default; use fb.kanaCount for actual count


def extractGlyphs(stageDirPath: str) -> list[bytes]:
    """Extract kana/kanji glyphs from STAGE.DIR. Returns list of 36-byte chunks."""
    return loadFont(stageDirPath).kanaGlyphs


def importGlyphsFromFolder(folder: str, kanaCount: int = GLYPH_COUNT) -> dict[int, bytes]:
    """Scan folder for glyph-NNN.png files, return dict of slot -> 36-byte glyph.

    Legacy wrapper around importKanaFromFolder.
    """
    return importKanaFromFolder(folder, kanaCount)


def injectGlyphs(stageDirPath: str, outputPath: str, glyphs: list[bytes]) -> None:
    """Patch kana/kanji glyphs into STAGE.DIR (legacy API — ASCII section unchanged)."""
    fb = loadFont(stageDirPath)
    if len(glyphs) != fb.kanaCount:
        raise ValueError(f"Expected {fb.kanaCount} glyphs, got {len(glyphs)}")
    fb.kanaGlyphs = list(glyphs)
    injectFont(stageDirPath, outputPath, fb)
