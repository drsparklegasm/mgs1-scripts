def lz77_compress(data, window_size=128):
    """
    Compresses data using a simple LZ77 algorithm.
    This was created by chatgpt. I wanted to see if we could
    replicate the lz77 compression used on graphics. As it stands,
    its very similar but the imlimentation is likely different.
    """
    compressed = []
    i = 0

    while i < len(data):
        # Look for the longest match in the sliding window
        match_distance = 0
        match_length = 0

        for j in range(max(0, i - window_size), i):
            length = 0
            while (i + length < len(data) and 
                   data[j + length] == data[i + length] and
                   length < 255):  # Limit match length
                length += 1

            if length > match_length:
                match_distance = i - j
                match_length = length

        # Add match or literal to the compressed output
        if match_length > 1:
            # (distance, length, next character)
            next_char = data[i + match_length] if i + match_length < len(data) else None
            compressed.append((match_distance, match_length, next_char))
            i += match_length + 1
        else:
            # Literal (distance=0, length=0, char)
            compressed.append((0, 0, data[i].to_bytes().hex()))
            i += 1

    return compressed

# Example: Compress 160 bytes of random data
data = bytes.fromhex('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f21fe9f11fb14000059000110fe3e60ff8fb2ffffffffcf0300d49f010040ff5f40ffcf0100b3ffffff3c0092ff6f0030fb6fd2ffff19f9150051fdffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')

compressed = lz77_compress(data)

# Print the compressed data
print("Compressed Data:")
for entry in compressed:
    print(entry)