import sys
import time

try:
    from unicornhatmini import UnicornHATMini
except ImportError:
    from unicornhatutils import UnicornHATMini

# Initialize the display
display = UnicornHATMini()
display.set_brightness(0.5)
display.clear()

# Define the bitmap font (5x7 ASCII font)
font = {
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
    '"': [0x00, 0x07, 0x00, 0x07, 0x00],
    '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
    ':': [0x24, 0x2A, 0x7F, 0x2A, 0x12],
    '%': [0x23, 0x13, 0x08, 0x64, 0x62],
    '&': [0x36, 0x49, 0x55, 0x22, 0x50],
    "'": [0x00, 0x05, 0x03, 0x00, 0x00],
    '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
    ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
    '*': [0x08, 0x2A, 0x1C, 0x2A, 0x08],
    '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
    ',': [0x00, 0x50, 0x30, 0x00, 0x00],
    '-': [0x08, 0x08, 0x08, 0x08, 0x08],
    '.': [0x00, 0x60, 0x60, 0x00, 0x00],
    '/': [0x20, 0x10, 0x08, 0x04, 0x02],
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
    '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46],
    '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
    '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
    '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36],
    '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00],
    ';': [0x00, 0x56, 0x36, 0x00, 0x00],
    '&lt;': [0x00, 0x08, 0x14, 0x22, 0x41],
    '=': [0x14, 0x14, 0x14, 0x14, 0x14],
    '&gt;': [0x41, 0x22, 0x14, 0x08, 0x00],
    '?': [0x02, 0x01, 0x51, 0x09, 0x06],
    '@': [0x32, 0x49, 0x79, 0x41, 0x3E],
    'A': [0x7E, 0x11, 0x11, 0x11, 0x7E],
    'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
    'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
    'F': [0x7F, 0x09, 0x09, 0x01, 0x01],
    'G': [0x3E, 0x41, 0x41, 0x51, 0x32],
    'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
    'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
    'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
    'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7F, 0x02, 0x04, 0x02, 0x7F],
    'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
    'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
    'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31],
    'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
    'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
    'W': [0x7F, 0x20, 0x18, 0x20, 0x7F],
    'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x03, 0x04, 0x78, 0x04, 0x03],
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    '[': [0x00, 0x00, 0x7F, 0x41, 0x41],
    ']': [0x41, 0x41, 0x7F, 0x00, 0x00],
    '^': [0x04, 0x02, 0x01, 0x02, 0x04],
    '_': [0x40, 0x40, 0x40, 0x40, 0x40],
    '`': [0x00, 0x01, 0x02, 0x04, 0x00],
    'a': [0x20, 0x54, 0x54, 0x54, 0x78],
    'b': [0x7F, 0x48, 0x44, 0x44, 0x38],
    'c': [0x38, 0x44, 0x44, 0x44, 0x20],
    'd': [0x38, 0x44, 0x44, 0x48, 0x7F],
    'e': [0x38, 0x54, 0x54, 0x54, 0x18],
    'f': [0x08, 0x7E, 0x09, 0x01, 0x02],
    'g': [0x08, 0x14, 0x54, 0x54, 0x3C],
    'h': [0x7F, 0x08, 0x04, 0x04, 0x78],
    'i': [0x00, 0x44, 0x7D, 0x40, 0x00],
    'j': [0x20, 0x40, 0x44, 0x3D, 0x00],
    'k': [0x00, 0x7F, 0x10, 0x28, 0x44],
    'l': [0x00, 0x41, 0x7F, 0x40, 0x00],
    'm': [0x7C, 0x04, 0x18, 0x04, 0x78],
    'n': [0x7C, 0x08, 0x04, 0x04, 0x78],
    'o': [0x38, 0x44, 0x44, 0x44, 0x38],
    'p': [0x7C, 0x14, 0x14, 0x14, 0x08],
    'q': [0x08, 0x14, 0x14, 0x18, 0x7C],
    'r': [0x7C, 0x08, 0x04, 0x04, 0x08],
    's': [0x48, 0x54, 0x54, 0x54, 0x20],
    't': [0x04, 0x3F, 0x44, 0x40, 0x20],
    'u': [0x3C, 0x40, 0x40, 0x20, 0x7C],
    'v': [0x1C, 0x20, 0x40, 0x20, 0x1C],
    'w': [0x3C, 0x40, 0x30, 0x40, 0x3C],
    'x': [0x44, 0x28, 0x10, 0x28, 0x44],
    'y': [0x0C, 0x50, 0x50, 0x50, 0x3C],
    'z': [0x44, 0x64, 0x54, 0x4C, 0x44],
    '{': [0x00, 0x08, 0x36, 0x41, 0x00],
    '|': [0x00, 0x00, 0x7F, 0x00, 0x00],
    '}': [0x00, 0x41, 0x36, 0x08, 0x00],
    '~': [0x08, 0x08, 0x2A, 0x1C, 0x08],
    # Geometric shapes
    '█': [0x7F, 0x7F, 0x7F, 0x7F, 0x7F],  # Square
    '○': [0x3E, 0x7F, 0x7F, 0x7F, 0x3E],  # Circle
    '▲': [0x08, 0x1C, 0x3E, 0x7F, 0x7F],  # Triangle
    '◆': [0x08, 0x1C, 0x3E, 0x1C, 0x08]   # Diamond
}

def render_char(char, x, y, color=(255, 255, 255)):
    """Render a character at the specified position."""
    bitmap = font.get(char.upper(), [])
    for row in range(len(bitmap)):
        for col in range(5):
            if bitmap[row] & (1 << (4 - col)):
                display.set_pixel(x + col, y + row, *color)

def clear_display():
    """Clear the display."""
    display.clear()
    display.show()

def main():
    """Main function to run the typewriter script."""
    x, y = 0, 0
    color = (255, 255, 255)  # White text color

    try:
        while True:
            char = sys.stdin.read(1)
            if char:
                if char == '\n':
                    # Handle line breaks
                    x = 0
                    y += 8
                    if y >= display.HEIGHT:
                        y = 0
                        clear_display()
                elif char == '\b':
                    # Handle backspace
                    if x > 0:
                        x -= 6
                        if x < 0:
                            x = display.WIDTH - 6
                            y -= 8
                            if y < 0:
                                y = display.HEIGHT - 8
                        for i in range(5):
                            for j in range(7):
                                display.set_pixel(x + i, y + j, 0, 0, 0)
                else:
                    # Render the character on the display
                    clear_display()  # Clear the display before rendering the new character
                    render_char(char, x, y, color)
                    x += 6
                    if x >= display.WIDTH:
                        x = 0
                        y += 8
                        if y >= display.HEIGHT:
                            y = 0
                            clear_display()
                display.show()
            else:
                time.sleep(0.1)  # Small delay when no input is available
    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C)
        clear_display()


if __name__ == '__main__':
    main()
