import numpy as np
import matplotlib.pyplot as plt

def display_graphic(hex_string):
    """Generate and display a character image from the graphics hex with correct scaling (12x12 grid)."""
    file_data = bytes.fromhex(hex_string)

    # Convert binary data to bit string
    bit_string = ''.join(format(byte, '08b') for byte in file_data)

    # Fixed 12x12 grid
    width, height = 12, 12  

    # Convert bit string to 2D pixel array
    pixel_grid = np.zeros((height, width), dtype=np.uint8)

    for i in range(len(bit_string) // 2):
        x, y = i % width, i // width
        bits = bit_string[i * 2 : i * 2 + 2]

        # Match the original TGA color mapping
        if bits == "00":
            pixel_grid[y, x] = 0     # Black
        elif bits == "01":
            pixel_grid[y, x] = 85    # Dark gray
        elif bits == "10":
            pixel_grid[y, x] = 170   # Light gray
        else:
            pixel_grid[y, x] = 255   # White

    # Display image with proper scaling (400% zoom)
    fig, ax = plt.subplots(figsize=(4, 4))  # 400% zoom
    ax.imshow(pixel_grid, cmap="gray", interpolation="nearest")
    ax.axis("off")
    plt.show()

print(f'Character display! Will loop and display a graphic per the hex. ')

while True:
    hexCharacters = input(f'\nPlease paste hex character string: ')
    if len(hexCharacters) == 72:
        display_graphic(hexCharacters)