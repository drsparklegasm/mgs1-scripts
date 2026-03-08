#!/usr/bin/env python3
"""
MGS1 Font Text Utilities

Functions for calculating pixel widths and laying out text using the
MGS1 PS1 font character widths from the font_manipulator toolkit.

Character width data comes from font_manipulator/data/original_widths.txt
(or new_widths.txt after editing). Each line is a hex width for a printable
ASCII character starting at 0x20 (space), in order.
"""

import os
import re

DEFAULT_WIDTHS_FILE = os.path.join("original_widths.txt")
DEFAULT_MAX_WIDTH = 260
DEFAULT_MAX_LINES = 4


def load_widths(widths_file=DEFAULT_WIDTHS_FILE):
    """Load character widths from a font_manipulator widths .txt file.

    Returns a dict mapping each printable ASCII character (str) to its
    pixel width (int). Lines in the file are formatted as:
        0A ; comment
    The file starts at 0x20 (space) and covers 96 characters.
    """
    widths = {}
    index = 0
    with open(widths_file, "r", encoding="utf-8") as f:
        for line in f:
            value = line.split(";")[0].strip()
            if not value:
                continue
            width = int(value, 16)
            char_code = 0x20 + index
            if char_code <= 0x7E:  # Standard printable ASCII range
                widths[chr(char_code)] = width
            index += 1
    return widths


def string_pixel_width(text, widths):
    """Calculate the total pixel width of a string.

    Characters not present in the widths dict (e.g. non-ASCII) contribute 0.

    Args:
        text:   The string to measure.
        widths: Dict mapping character to pixel width, from load_widths().

    Returns:
        Total pixel width as int.
    """
    return sum(widths.get(ch, 0) for ch in text)


def wrap_text(text, widths, max_width=DEFAULT_MAX_WIDTH):
    """Word-wrap text so no line exceeds max_width pixels.

    Splits on spaces only (no hyphenation). A single word wider than
    max_width will appear on its own line without truncation.

    Args:
        text:      The string to wrap.
        widths:    Dict mapping character to pixel width, from load_widths().
        max_width: Maximum line width in pixels (default 260).

    Returns:
        List of strings, one per line.
    """
    space_width = widths.get(" ", 4)
    words = text.split(" ")
    lines = []
    current_words = []
    current_width = 0

    for word in words:
        word_width = string_pixel_width(word, widths)

        if not current_words:
            current_words.append(word)
            current_width = word_width
        elif current_width + space_width + word_width <= max_width:
            current_words.append(word)
            current_width += space_width + word_width
        else:
            lines.append(" ".join(current_words))
            current_words = [word]
            current_width = word_width

    if current_words:
        lines.append(" ".join(current_words))

    return lines


def split_into_blocks(text, widths, max_width=DEFAULT_MAX_WIDTH, max_lines=DEFAULT_MAX_LINES, min_lines=2):
    """Split text into at most two dialogue blocks if it exceeds max_lines lines.

    First tries every sentence boundary (after '. ', '! ', '? ') and picks
    the one that keeps both blocks within max_lines while being most balanced.
    Candidate sentence splits where block A is shorter than min_lines are
    skipped to avoid fragments like "According to Mr." becoming a full screen.
    Falls back to a word-boundary split at the point where block A would
    overflow into a 5th line if no valid sentence split exists.

    Args:
        text:      The full text to lay out.
        widths:    Dict mapping character to pixel width, from load_widths().
        max_width: Maximum line width in pixels (default 260).
        max_lines: Maximum lines per block before splitting (default 4).
        min_lines: Minimum lines required in block A for a sentence split to
                   be accepted (default 2). Prevents very short first blocks.

    Returns:
        List of one or two strings. Each string uses newlines between lines.
    """
    lines = wrap_text(text, widths, max_width)
    if len(lines) <= max_lines:
        return ["\n".join(lines)]

    # Collect all sentence-end split positions (after '. ', '! ', '? ')
    sentence_splits = [m.end() for m in re.finditer(r'[.!?]\s+', text)]

    best_pos = None
    best_balance = float("inf")

    for pos in sentence_splits:
        a = text[:pos].strip()
        b = text[pos:].strip()
        if not a or not b:
            continue
        a_lines = wrap_text(a, widths, max_width)
        b_lines = wrap_text(b, widths, max_width)
        if len(a_lines) >= min_lines and len(a_lines) <= max_lines and len(b_lines) <= max_lines:
            balance = abs(len(a_lines) - len(b_lines))
            if balance < best_balance:
                best_balance = balance
                best_pos = pos

    if best_pos is not None:
        block_a = text[:best_pos].strip()
        block_b = text[best_pos:].strip()
    else:
        # No sentence boundary works — split at the last word that keeps
        # block A within max_lines.
        words = text.split(" ")
        split_idx = 1
        for i in range(1, len(words)):
            candidate = " ".join(words[:i])
            if len(wrap_text(candidate, widths, max_width)) <= max_lines:
                split_idx = i
            else:
                break
        block_a = " ".join(words[:split_idx])
        block_b = " ".join(words[split_idx:])

    return [
        "\n".join(wrap_text(block_a, widths, max_width)),
        "\n".join(wrap_text(block_b, widths, max_width)),
    ]


def main():
    """Interactive loop: prompt for text, display wrapped blocks, repeat."""
    widths = load_widths()
    print("MGS1 Font Text Layout  (max 260 px / 4 lines per block)")
    print("Type your text and press Enter. Ctrl+C or blank line to quit.\n")

    while True:
        try:
            text = input("Text: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not text:
            break

        blocks = split_into_blocks(text, widths)

        print()
        for i, block in enumerate(blocks, 1):
            if len(blocks) > 1:
                print(f"  [ Block {i} ]")
            lines = block.split("\n")
            for line in lines:
                px = string_pixel_width(line, widths)
                print(f"  {px:>3} px | {line}")
        print()


if __name__ == "__main__":
    main()
