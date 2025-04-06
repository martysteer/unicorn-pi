#!/usr/bin/env python3
"""
Realtime Text Display for Unicorn HAT Mini

A simple script that displays single characters typed in real-time.
Each keypress replaces what's currently shown on the display.

Press Ctrl+C to exit.
"""

import sys
from PIL import Image, ImageDraw, ImageFont

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

def render_char(char, display):
    """Render a single character on the Unicorn HAT Mini"""
    # Clear the display first
    display.clear()
    
    # Get display dimensions
    width, height = display.get_shape()
    
    # Create a blank image
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if necessary
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 8)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw the character centered on the display
    try:
        # For newer PIL versions
        text_width, text_height = draw.textbbox((0, 0), char, font=font)[2:4]
    except AttributeError:
        # Fallback for older PIL versions
        text_width, text_height = draw.textsize(char, font=font)
    
    # Center the character
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw the character in white
    draw.text((x, y), char, fill=(255, 255, 255), font=font)
    
    # Set pixels directly on the display
    for y in range(height):
        for x in range(width):
            r, g, b = image.getpixel((x, y))
            display.set_pixel(x, y, r, g, b)
    
    # Update the display
    display.show()

def main():
    # Initialize the Unicorn HAT Mini
    display = UnicornHATMini()
    display.set_brightness(0.5)
    display.clear()
    display.show()
    
    print("Realtime Text Display for Unicorn HAT Mini")
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
            
            # Render the character on the display
            render_char(char, display)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clear the display
        display.clear()
        display.show()
        print("\nDisplay cleared.")

if __name__ == "__main__":
    main()