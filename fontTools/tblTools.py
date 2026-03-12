"""
MGS1 Table File Tools — .tbl file support for custom font encoding

Standard ROM hacking .tbl format: one line per entry, HEXCODE=CHARACTER.
Lines starting with # are comments. Blank lines are ignored.

The .tbl maps the game's 2-byte text encoding to Unicode characters:
  - 8101-8153: hiragana (83 slots, font positions 0-82)
  - 8201-8256: katakana (86 slots, font positions 83-168)
  - 9001-90ff, 9101-9111: kanji/punctuation (271 slots, font positions 169-439)

When a translator replaces font glyphs, they update the .tbl so the encoder
knows which byte code produces which character in the modified font.
"""

import translation.characters as characters

HIRAGANA_COUNT = 83
KATAKANA_COUNT = 86
KANJI_START = HIRAGANA_COUNT + KATAKANA_COUNT  # 169

# Legacy constant — use FontBlock.kanaCount for actual glyph count
GLYPH_COUNT = 440


def slotToHexCode(slot: int) -> str:
    """Map a font glyph slot index to its 2-byte hex code string.

    Returns the 4-character hex string used in the game's text encoding,
    e.g. '8101' for hiragana slot 0, '8201' for katakana slot 0, '9001' for
    the first kanji/punctuation slot. Works for any non-negative slot index.
    """
    if slot < 0:
        raise ValueError(f"Slot {slot} out of range (must be >= 0)")

    if slot < HIRAGANA_COUNT:
        # Hiragana: 0x81 prefix, second byte 01-53
        return f'81{slot + 1:02x}'
    elif slot < KANJI_START:
        # Katakana: 0x82 prefix, second byte 01-56
        katIdx = slot - HIRAGANA_COUNT
        return f'82{katIdx + 1:02x}'
    else:
        # Kanji/punctuation: sequential from 9001, skipping 9100
        kanjiIdx = slot - KANJI_START  # 0-based index into kanji section
        # Codes go 9001..90ff (255 codes), then 9101..9111 (17 codes)
        # 9100 is skipped (was a spurious entry)
        if kanjiIdx < 255:
            code = 0x9001 + kanjiIdx
        else:
            # After 90ff, skip 9100, continue at 9101
            code = 0x9101 + (kanjiIdx - 255)
        return f'{code:04x}'


def hexCodeToSlot(hexCode: str) -> int:
    """Map a 4-character hex code string back to a font glyph slot index (0-439).

    Returns -1 if the hex code doesn't correspond to a font glyph slot.
    """
    code = int(hexCode, 16)
    highByte = (code >> 8) & 0xFF
    lowByte = code & 0xFF

    if highByte == 0x81 and 0x01 <= lowByte <= 0x53:
        return lowByte - 1
    elif highByte == 0x82 and 0x01 <= lowByte <= 0x56:
        return HIRAGANA_COUNT + lowByte - 1
    elif highByte == 0x90 and 0x01 <= lowByte <= 0xFF:
        return KANJI_START + (lowByte - 1)
    elif highByte == 0x91 and 0x01 <= lowByte <= 0x11:
        return KANJI_START + 255 + (lowByte - 1)
    return -1


def generateDefaultTbl() -> dict[str, str]:
    """Generate a .tbl mapping from the current characters.py data.

    Returns a dict mapping hex code (e.g. '8101') to character (e.g. 'ぁ').
    Covers all 440 font glyph slots.
    """
    mapping = {}

    # Hiragana
    for key, char in characters.hiragana.items():
        hexCode = f'81{key}'
        mapping[hexCode] = char

    # Katakana
    for key, char in characters.katakana.items():
        hexCode = f'82{key}'
        mapping[hexCode] = char

    # Kanji/punctuation — only the font-resident range (>= 0x9001, < 0x9a01)
    for key, char in characters.kanji.items():
        code = int(key, 16)
        if 0x9001 <= code <= 0x9111:
            mapping[key] = char

    return mapping


def loadTbl(path: str) -> dict[str, str]:
    """Parse a .tbl file. Returns dict mapping hex code -> character."""
    with open(path, 'r', encoding='utf-8') as f:
        return loadTblFromString(f.read())


def loadTblFromString(text: str) -> dict[str, str]:
    """Parse .tbl content from a string. Returns dict mapping hex code -> character."""
    mapping = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        hexCode, char = line.split('=', 1)
        hexCode = hexCode.strip().lower()
        mapping[hexCode] = char
    return mapping


def saveTbl(path: str, mapping: dict[str, str]) -> None:
    """Write a .tbl file from a hex-to-character dict."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(tblToString(mapping))


def tblToString(mapping: dict[str, str]) -> str:
    """Serialize a .tbl mapping to string content."""
    lines = ['# MGS1 Font Table File',
             '# Format: HEXCODE=CHARACTER',
             '# Hiragana: 8101-8153, Katakana: 8201-8256, Kanji: 9001-9111',
             '']

    # Sort by hex code for readability
    sortedKeys = sorted(mapping.keys(), key=lambda k: int(k, 16))

    lastPrefix = None
    for hexCode in sortedKeys:
        prefix = hexCode[:2]
        if prefix != lastPrefix:
            if lastPrefix is not None:
                lines.append('')
            lastPrefix = prefix
        lines.append(f'{hexCode}={mapping[hexCode]}')

    lines.append('')
    return '\n'.join(lines)


def tblToEncoderOverrides(tblMapping: dict[str, str]) -> dict[str, str]:
    """Convert a .tbl forward mapping (hex->char) to a reverse mapping (char->hex)
    suitable for use as an override dict in encodeJapaneseHex.

    The returned dict maps character -> hex code string. When encoding, if a
    character is found here, the encoder emits the corresponding bytes instead
    of using the default characters.py lookups.
    """
    overrides = {}
    for hexCode, char in tblMapping.items():
        # Last-wins for duplicate characters (shouldn't happen in a well-formed .tbl)
        overrides[char] = hexCode
    return overrides
