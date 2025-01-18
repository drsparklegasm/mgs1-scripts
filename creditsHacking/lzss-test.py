def lzss_compress(data, window_size=256, lookahead_buffer_size=15):
    """
    Compress a bytes object using a simple LZSS algorithm.

    Args:
        data (bytes): The data to compress.
        window_size (int): The size of the sliding window.
        lookahead_buffer_size (int): The size of the lookahead buffer.

    Returns:
        list[tuple]: The compressed data as a list of (offset, length, next_byte) tuples.
    """
    compressed = []
    i = 0

    while i < len(data):
        match_distance = 0
        match_length = 0

        # Sliding window start
        start_window = max(0, i - window_size)

        # Look for the longest match in the sliding window
        for j in range(start_window, i):
            length = 0
            while (length < lookahead_buffer_size and 
                   i + length < len(data) and 
                   data[j + length] == data[i + length]):
                length += 1

            if length > match_length:
                match_distance = i - j
                match_length = length

        # If a match is found, add it as a (distance, length, next byte) tuple
        if match_length > 1:
            next_byte = data[i + match_length] if i + match_length < len(data) else None
            compressed.append((match_distance, match_length, next_byte))
            i += match_length + 1
        else:
            # Add a literal (distance=0, length=0, next_byte)
            compressed.append((0, 0, data[i]))
            i += 1

    return compressed

# Example usage
data = b"ABABABABCCCCCCCCCCCCCCCCABABABABABAB"

compressed_data = lzss_compress(data)
print("Compressed Data:")
for entry in compressed_data:
    print(entry)