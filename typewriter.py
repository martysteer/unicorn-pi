#!/usr/bin/env python3
"""
Realtime Text Display for Unicorn HAT Mini

A simple script that displays single characters typed in real-time.
Each keypress replaces what's currently shown on the display.

Features:
- Uses a custom 5x5 bitmap font for a retro pixel art look
- Each new character appears in a random color
- Characters are centered on the display

Press Ctrl+C to exit.
"""

import sys
import random
from PIL import Image, ImageDraw

# Try to import the Unicorn HAT Mini library
try:
    from unicornhatmini import UnicornHATMini
except ImportError:
    try:
        # Try proxy implementation for development
        from proxyunicornhatmini import UnicornHATMiniBase as UnicornHATMini
    except ImportError:
        print("Error: Could not import UnicornHATMini library.")
        print("Install with: sudo pip3 install unicornhatmini")
        sys.exit(1)

# Define a compact 5x5 bitmap font using hex values
# Each character is represented by a list of 5 hex values, one for each row
# Each hex value represents a 5-bit pattern where 1 = pixel on, 0 = pixel off
BITMAP_FONT = {
    'A': [0x0E, 0x11, 0x1F, 0x11, 0x11],
    'B': [0x1E, 0x11, 0x1E, 0x11, 0x1E],
    'C': [0x0E, 0x11, 0x10, 0x11, 0x0E],
    'D': [0x1E, 0x09, 0x09, 0x09, 0x1E],
    'E': [0x1F, 0x10, 0x1E, 0x10, 0x1F],
    'F': [0x1F, 0x10, 0x1E, 0x10, 0x10],
    'G': [0x0E, 0x10, 0x17, 0x11, 0x0E],
    'H': [0x11, 0x11, 0x1F, 0x11, 0x11],
    'I': [0x0E, 0x04, 0x04, 0x04, 0x0E],
    'J': [0x07, 0x02, 0x02, 0x12, 0x0C],
    'K': [0x11, 0x12, 0x1C, 0x12, 0x11],
    'L': [0x10, 0x10, 0x10, 0x10, 0x1F],
    'M': [0x11, 0x1B, 0x15, 0x11, 0x11],
    'N': [0x11, 0x19, 0x15, 0x13, 0x11],
    'O': [0x0E, 0x11, 0x11, 0x11, 0x0E],
    'P': [0x1E, 0x11, 0x1E, 0x10, 0x10],
    'Q': [0x0E, 0x11, 0x15, 0x12, 0x0D],
    'R': [0x1E, 0x11, 0x1E, 0x14, 0x13],
    'S': [0x0F, 0x10, 0x0E, 0x01, 0x1E],
    'T': [0x1F, 0x04, 0x04, 0x04, 0x04],
    'U': [0x11, 0x11, 0x11, 0x11, 0x0E],
    'V': [0x11, 0x11, 0x11, 0x0A, 0x04],
    'W': [0x11, 0x11, 0x15, 0x15, 0x0A],
    'X': [0x11, 0x0A, 0x04, 0x0A, 0x11],
    'Y': [0x11, 0x0A, 0x04, 0x04, 0x04],
    'Z': [0x1F, 0x02, 0x04, 0x08, 0x1F],
    '0': [0x0E, 0x13, 0x15, 0x19, 0x0E],
    '1': [0x04, 0x0C, 0x04, 0x04, 0x0E],
    '2': [0x0E, 0x01, 0x0E, 0x10, 0x1F],
    '3': [0x1F, 0x02, 0x0E, 0x01, 0x1E],
    '4': [0x12, 0x12, 0x1F, 0x02, 0x02],
    '5': [0x1F, 0x10, 0x1E, 0x01, 0x1E],
    '6': [0x0E, 0x10, 0x1E, 0x11, 0x0E],
    '7': [0x1F, 0x01, 0x02, 0x04, 0x08],
    '8': [0x0E, 0x11, 0x0E, 0x11, 0x0E],
    '9': [0x0E, 0x11, 0x0F, 0x01, 0x0E],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    '.': [0x00, 0x00, 0x00, 0x00, 0x04],
    ',': [0x00, 0x00, 0x00, 0x04, 0x08],
    '!': [0x04, 0x04, 0x04, 0x00, 0x04],
    '?': [0x0E, 0x01, 0x06, 0x00, 0x04],
    ':': [0x00, 0x04, 0x00, 0x04, 0x00],
    ';': [0x00, 0x04, 0x00, 0x04, 0x08],
    '-': [0x00, 0x00, 0x1F, 0x00, 0x00],
    '_': [0x00, 0x00, 0x00, 0x00, 0x1F],
    '+': [0x00, 0x04, 0x1F, 0x04, 0x00],
    '=': [0x00, 0x1F, 0x00, 0x1F, 0x00],
    '/': [0x01, 0x02, 0x04, 0x08, 0x10],
    '\\': [0x10, 0x08, 0x04, 0x02, 0x01],
    '*': [0x11, 0x0A, 0x04, 0x0A, 0x11],
    '(': [0x06, 0x08, 0x08, 0x08, 0x06],
    ')': [0x0C, 0x02, 0x02, 0x02, 0x0C],
    '[': [0x0E, 0x08, 0x08, 0x08, 0x0E],
    ']': [0x0E, 0x02, 0x02, 0x02, 0x0E],
    '{': [0x06, 0x08, 0x0C, 0x08, 0x06],
    '}': [0x0C, 0x02, 0x06, 0x02, 0x0C],
    '<': [0x02, 0x04, 0x08, 0x04, 0x02],
    '>': [0x08, 0x04, 0x02, 0x04, 0x08],
    '@': [0x0E, 0x11, 0x17, 0x10, 0x0F],
    '#': [0x0A, 0x1F, 0x0A, 0x1F, 0x0A],
    '$': [0x04, 0x0F, 0x14, 0x0F, 0x04],
    '%': [0x11, 0x02, 0x04, 0x08, 0x11],
    '&': [0x08, 0x14, 0x08, 0x15, 0x0A],
    '\'': [0x06, 0x06, 0x00, 0x00, 0x00],
    '"': [0x0A, 0x0A, 0x00, 0x00, 0x00],
    '`': [0x08, 0x04, 0x00, 0x00, 0x00],
    '~': [0x00, 0x08, 0x15, 0x02, 0x00],
    '^': [0x04, 0x0A, 0x00, 0x00, 0x00],
    '|': [0x04, 0x04, 0x04, 0x04, 0x04],
}

def get_random_color():
    """Generate a vibrant random RGB color"""
    # Use more vibrant colors by avoiding dark/low values
    r = random.randint(100, 255)
    g = random.randint(100, 255)
    b = random.randint(100, 255)
    return (r, g, b)

def getch():
    """Get a single character from stdin without requiring Enter"""
    try:
        # For Unix/Linux/MacOS
        import termios
        import tty
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    except ImportError:
        # For Windows
        import msvcrt
        return msvcrt.getch().decode('utf-8')

def render_bitmap_char(char, display, color=None):
    """Render a character using the bitmap font on the Unicorn HAT Mini"""
    # Generate a random color if none provided
    if color is None:
        color = get_random_color()
    
    # Clear the display first
    display.clear()
    
    # Get display dimensions
    width, height = display.get_shape()
    
    # Convert to uppercase for our font (only uppercase is defined)
    char = char.upper()
    
    # If character is not in our font, use a space
    if char not in BITMAP_FONT:
        char = ' '
    
    # Get the bitmap pattern for the character
    pattern = BITMAP_FONT[char]
    
    # Number of bits per row (5 for our font)
    char_width = 5
    char_height = len(pattern)
    
    # Calculate position to center the character on the display
    x_offset = (width - char_width) // 2
    y_offset = (height - char_height) // 2
    
    # Set pixels based on the bitmap pattern
    for y in range(char_height):
        # Get the hex value for this row
        row_pattern = pattern[y]
        
        # Convert the hex value to binary and check each bit
        for x in range(char_width):
            # Check if bit is set (1), starting from MSB
            # The bit position for a 5-bit wide font is: 4, 3, 2, 1, 0
            bit_position = char_width - 1 - x
            if row_pattern & (1 << bit_position):
                display.set_pixel(x + x_offset, y + y_offset, *color)
    
    # Update the display
    display.show()
    
    # Return the color used (for display in terminal)
    return color

def main():
    # Initialize the Unicorn HAT Mini
    display = UnicornHATMini()
    display.set_brightness(0.5)
    display.clear()
    display.show()
    
    print("Colorful Bitmap Font Typewriter for Unicorn HAT Mini")
    print("Type characters to display them in random colors. Press Ctrl+C to exit.")
    
    try:
        while True:
            char = getch()
            
            # Check for Ctrl+C (ASCII value 3)
            if ord(char) == 3:
                raise KeyboardInterrupt
            
            # Generate a random color for this character
            color = get_random_color()
            
            # Echo the character to the terminal with color info
            sys.stdout.write(f"{char} [RGB: {color[0]},{color[1]},{color[2]}]\n")
            sys.stdout.flush()
            
            # Render the character on the display using our bitmap font
            render_bitmap_char(char, display, color)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clear the display
        display.clear()
        display.show()
        print("\nDisplay cleared.")

if __name__ == "__main__":
    main()