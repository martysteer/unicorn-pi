#!/usr/bin/env python3
"""
Realtime Text Display for Unicorn HAT Mini

A simple script that displays single characters typed in real-time.
Each keypress replaces what's currently shown on the display.

Uses a custom bitmap font for a retro pixel art look.

Press Ctrl+C to exit.
"""

import sys
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

# Define a basic 5x7 bitmap font
# Each character is defined as a list of rows, where each row is a binary pattern
# 1 = pixel on, 0 = pixel off
BITMAP_FONT = {
    'A': [
        "01110",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001"
    ],
    'B': [
        "11110",
        "10001",
        "10001",
        "11110",
        "10001",
        "10001",
        "11110"
    ],
    'C': [
        "01110",
        "10001",
        "10000",
        "10000",
        "10000",
        "10001",
        "01110"
    ],
    'D': [
        "11110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "11110"
    ],
    'E': [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111"
    ],
    'F': [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "10000"
    ],
    'G': [
        "01110",
        "10001",
        "10000",
        "10111",
        "10001",
        "10001",
        "01111"
    ],
    'H': [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001"
    ],
    'I': [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111"
    ],
    'J': [
        "00111",
        "00010",
        "00010",
        "00010",
        "00010",
        "10010",
        "01100"
    ],
    'K': [
        "10001",
        "10010",
        "10100",
        "11000",
        "10100",
        "10010",
        "10001"
    ],
    'L': [
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "11111"
    ],
    'M': [
        "10001",
        "11011",
        "10101",
        "10001",
        "10001",
        "10001",
        "10001"
    ],
    'N': [
        "10001",
        "11001",
        "10101",
        "10101",
        "10011",
        "10001",
        "10001"
    ],
    'O': [
        "01110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110"
    ],
    'P': [
        "11110",
        "10001",
        "10001",
        "11110",
        "10000",
        "10000",
        "10000"
    ],
    'Q': [
        "01110",
        "10001",
        "10001",
        "10001",
        "10101",
        "10010",
        "01101"
    ],
    'R': [
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001"
    ],
    'S': [
        "01111",
        "10000",
        "10000",
        "01110",
        "00001",
        "00001",
        "11110"
    ],
    'T': [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100"
    ],
    'U': [
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110"
    ],
    'V': [
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01010",
        "00100"
    ],
    'W': [
        "10001",
        "10001",
        "10001",
        "10101",
        "10101",
        "11011",
        "10001"
    ],
    'X': [
        "10001",
        "10001",
        "01010",
        "00100",
        "01010",
        "10001",
        "10001"
    ],
    'Y': [
        "10001",
        "10001",
        "01010",
        "00100",
        "00100",
        "00100",
        "00100"
    ],
    'Z': [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
        "10000",
        "11111"
    ],
    '0': [
        "01110",
        "10001",
        "10011",
        "10101",
        "11001",
        "10001",
        "01110"
    ],
    '1': [
        "00100",
        "01100",
        "00100",
        "00100",
        "00100",
        "00100",
        "01110"
    ],
    '2': [
        "01110",
        "10001",
        "00001",
        "00010",
        "00100",
        "01000",
        "11111"
    ],
    '3': [
        "11111",
        "00010",
        "00100",
        "00010",
        "00001",
        "10001",
        "01110"
    ],
    '4': [
        "00010",
        "00110",
        "01010",
        "10010",
        "11111",
        "00010",
        "00010"
    ],
    '5': [
        "11111",
        "10000",
        "11110",
        "00001",
        "00001",
        "10001",
        "01110"
    ],
    '6': [
        "00110",
        "01000",
        "10000",
        "11110",
        "10001",
        "10001",
        "01110"
    ],
    '7': [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
        "01000",
        "01000"
    ],
    '8': [
        "01110",
        "10001",
        "10001",
        "01110",
        "10001",
        "10001",
        "01110"
    ],
    '9': [
        "01110",
        "10001",
        "10001",
        "01111",
        "00001",
        "00010",
        "01100"
    ],
    ' ': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000"
    ],
    '.': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00100"
    ],
    ',': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00100",
        "01000"
    ],
    '!': [
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00000",
        "00100"
    ],
    '?': [
        "01110",
        "10001",
        "00001",
        "00010",
        "00100",
        "00000",
        "00100"
    ],
    ':': [
        "00000",
        "00100",
        "00000",
        "00000",
        "00000",
        "00100",
        "00000"
    ],
    ';': [
        "00000",
        "00100",
        "00000",
        "00000",
        "00000",
        "00100",
        "01000"
    ],
    '-': [
        "00000",
        "00000",
        "00000",
        "11111",
        "00000",
        "00000",
        "00000"
    ],
    '_': [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "11111"
    ],
    '+': [
        "00000",
        "00100",
        "00100",
        "11111",
        "00100",
        "00100",
        "00000"
    ],
    '=': [
        "00000",
        "00000",
        "11111",
        "00000",
        "11111",
        "00000",
        "00000"
    ],
    '/': [
        "00000",
        "00001",
        "00010",
        "00100",
        "01000",
        "10000",
        "00000"
    ],
    '\\': [
        "00000",
        "10000",
        "01000",
        "00100",
        "00010",
        "00001",
        "00000"
    ],
    '*': [
        "00000",
        "10001",
        "01010",
        "00100",
        "01010",
        "10001",
        "00000"
    ],
    '(': [
        "00010",
        "00100",
        "01000",
        "01000",
        "01000",
        "00100",
        "00010"
    ],
    ')': [
        "01000",
        "00100",
        "00010",
        "00010",
        "00010",
        "00100",
        "01000"
    ],
    '[': [
        "01110",
        "01000",
        "01000",
        "01000",
        "01000",
        "01000",
        "01110"
    ],
    ']': [
        "01110",
        "00010",
        "00010",
        "00010",
        "00010",
        "00010",
        "01110"
    ],
    '{': [
        "00110",
        "00100",
        "00100",
        "01000",
        "00100",
        "00100",
        "00110"
    ],
    '}': [
        "01100",
        "00100",
        "00100",
        "00010",
        "00100",
        "00100",
        "01100"
    ],
    '<': [
        "00010",
        "00100",
        "01000",
        "10000",
        "01000",
        "00100",
        "00010"
    ],
    '>': [
        "01000",
        "00100",
        "00010",
        "00001",
        "00010",
        "00100",
        "01000"
    ],
    # Add more characters as needed
}

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

def render_bitmap_char(char, display, color=(255, 255, 255)):
    """Render a character using the bitmap font on the Unicorn HAT Mini"""
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
    
    # Calculate pixel size and offset to center the character
    char_width = len(pattern[0])
    char_height = len(pattern)
    
    # Calculate position to center the character on the display
    x_offset = (width - char_width) // 2
    y_offset = (height - char_height) // 2
    
    # Set pixels based on the bitmap pattern
    for y in range(char_height):
        for x in range(char_width):
            if y < len(pattern) and x < len(pattern[y]):
                if pattern[y][x] == '1':
                    display.set_pixel(x + x_offset, y + y_offset, *color)
    
    # Update the display
    display.show()

def main():
    # Initialize the Unicorn HAT Mini
    display = UnicornHATMini()
    display.set_brightness(0.5)
    display.clear()
    display.show()
    
    print("Bitmap Font Typewriter for Unicorn HAT Mini")
    print("Type characters to display them. Press Ctrl+C to exit.")
    
    try:
        while True:
            char = getch()
            
            # Check for Ctrl+C (ASCII value 3)
            if ord(char) == 3:
                raise KeyboardInterrupt
            
            # Echo the character to the terminal
            sys.stdout.write(char)
            sys.stdout.flush()
            
            # Render the character on the display using our bitmap font
            render_bitmap_char(char, display)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clear the display
        display.clear()
        display.show()
        print("\nDisplay cleared.")

if __name__ == "__main__":
    main()