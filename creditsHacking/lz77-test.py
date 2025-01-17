def lz77_compress(data, window_size=20):
    """
    Compresses data using a simple LZ77 algorithm.
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
            compressed.append((0, 0, data[i]))
            i += 1

    return compressed

# Example: Compress 160 bytes of random data
data = bytes.fromhex('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6f00f95f00fb049999bd6940a9ff0a21ff6fb0ffffffff2e708b709f509ab9ff1d01fccf408a12fdffff23ba33ff07b419e25fc0ffff09f9057604e3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')

compressed = lz77_compress(data)

# Print the compressed data
print("Compressed Data:")
for entry in compressed:
    print(entry)