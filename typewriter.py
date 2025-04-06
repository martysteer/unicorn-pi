#!/usr/bin/env python3
"""
Animated Text Display for Unicorn HAT Mini

A script that displays typed characters with various animation styles.
Each keypress updates the display with the new character.

Animation modes:
- 'push': Each new character pushes in from the right, moving existing text left
- 'pop': Characters build up from right to left, creating a text queue
- 'marquee': Text scrolls continuously from right to left in a loop

Features:
- Uses a custom 5x5 bitmap font for a retro pixel art look
- Characters appear in random colors
- Command-line arguments to select animation mode and adjust speeds

Usage:
    python typewriter.py --type [push|pop|marquee] [--speed SPEED]

Press Ctrl+C to exit.
"""

import sys
import time
import random
import math
import argparse
from collections import deque

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

# Constants
CHAR_WIDTH = 5  # Width of each character in pixels
CHAR_HEIGHT = 5  # Height of each character in pixels
CHAR_SPACING = 1  # Space between characters

def get_random_color():
    """Generate a vibrant random RGB color"""
    # Use more vibrant colors by avoiding dark/low values
    r = random.randint(100, 255)
    g = random.randint(100, 255)
    b = random.randint(100, 255)
    return (r, g, b)

def interpolate_colors(color1, color2, factor):
    """
    Linearly interpolate between two colors
    
    Args:
        color1: First RGB color tuple
        color2: Second RGB color tuple
        factor: Value between 0.0 and 1.0 (0 = color1, 1 = color2)
        
    Returns:
        Interpolated RGB color tuple
    """
    # Ensure factor is between 0 and 1
    factor = max(0.0, min(1.0, factor))
    
    # Interpolate each component
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    
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

def render_bitmap_char(display, char, position, color):
    """
    Render a single character at a specific position
    
    Args:
        display: UnicornHATMini instance
        char: Character to render
        position: (x, y) tuple for top-left position
        color: RGB color tuple
    """
    # Allow for floating-point positions for smooth animation
    x_pos, y_pos = position
    
    # Convert to uppercase for our font (only uppercase is defined)
    char = char.upper()
    
    # If character is not in our font, use a space
    if char not in BITMAP_FONT:
        char = ' '
    
    # Get the bitmap pattern for the character
    pattern = BITMAP_FONT[char]
    
    # Set pixels based on the bitmap pattern
    for y in range(CHAR_HEIGHT):
        # Get the hex value for this row
        row_pattern = pattern[y]
        
        # Check each bit in the row
        for x in range(CHAR_WIDTH):
            # Check if bit is set (1), starting from MSB
            bit_position = CHAR_WIDTH - 1 - x
            if row_pattern & (1 << bit_position):
                # Calculate the actual position on the display (rounded to nearest integer)
                pixel_x = int(x_pos + x + 0.5)
                pixel_y = int(y_pos + y + 0.5)
                
                # Check if the pixel is within display bounds
                if 0 <= pixel_x < display.get_shape()[0] and 0 <= pixel_y < display.get_shape()[1]:
                    display.set_pixel(pixel_x, pixel_y, *color)

def clear_display(display):
    """Clear the display and show it"""
    display.clear()
    display.show()

def animate_push(display, char_queue, speed_factor=1.0):
    """
    Animate a new character pushing in from the right with smooth motion
    
    Args:
        display: UnicornHATMini instance
        char_queue: List of (char, color) tuples
        speed_factor: Speed multiplier (lower is slower)
    """
    width, height = display.get_shape()
    
    # Calculate the total width of the character sequence
    total_width = len(char_queue) * (CHAR_WIDTH + CHAR_SPACING) - CHAR_SPACING
    
    # Number of animation steps (more steps = smoother animation)
    steps = int(20 / speed_factor)  # Increased steps for smoother animation
    
    # Animate the push
    for step in range(steps + 1):  # +1 to ensure we reach the final position
        display.clear()
        
        # Calculate progress factor (0.0 to 1.0)
        progress = step / steps
        
        # Use easing function for smoother motion
        # This creates a slight ease-in, ease-out effect
        ease_factor = 0.5 - 0.5 * math.cos(progress * math.pi)
        
        # Calculate offset for this animation step
        offset = (CHAR_WIDTH + CHAR_SPACING) * (1.0 - ease_factor)
        
        # Draw each character at its offset position
        for i, (char, color) in enumerate(char_queue):
            # Calculate the x position for this character
            x_pos = width - total_width + (i * (CHAR_WIDTH + CHAR_SPACING)) - offset
            
            # Only draw if it's at least partially on screen
            if x_pos + CHAR_WIDTH > 0:
                render_bitmap_char(display, char, (x_pos, 1), color)
        
        # Update the display
        display.show()
        
        # Sleep longer for slower animation (adjusted by speed_factor)
        time.sleep(0.01 / speed_factor)

def animate_pop(display, char_queue, speed_factor=1.0):
    """
    Animate a new character appearing from the right with a smooth transition
    
    Args:
        display: UnicornHATMini instance
        char_queue: List of (char, color) tuples
        speed_factor: Speed multiplier (lower is slower)
    """
    width, height = display.get_shape()
    
    # Calculate how many characters we can fit on screen
    max_chars = (width + CHAR_SPACING) // (CHAR_WIDTH + CHAR_SPACING)
    
    # Take only the characters that will fit on screen
    visible_chars = char_queue[-max_chars:] if len(char_queue) > max_chars else char_queue
    
    # Calculate the total width of the visible character sequence
    total_width = len(visible_chars) * (CHAR_WIDTH + CHAR_SPACING) - CHAR_SPACING
    
    # Previous positions (for smooth transition)
    prev_positions = {}
    
    # Number of animation steps
    steps = int(15 / speed_factor)
    
    # First, get the final positions
    final_positions = {}
    for i, (char, _) in enumerate(visible_chars):
        final_positions[char] = width - total_width + (i * (CHAR_WIDTH + CHAR_SPACING))
    
    # For each animation step
    for step in range(steps + 1):  # +1 to ensure we reach the final position
        display.clear()
        
        # Calculate progress factor (0.0 to 1.0)
        progress = step / steps
        
        # Use easing function for smoother motion
        ease_factor = 0.5 - 0.5 * math.cos(progress * math.pi)
        
        # Draw each character with interpolated position
        for i, (char, color) in enumerate(visible_chars):
            # Get final position
            final_x = final_positions[char]
            
            # If this is a new character, start it from off-screen
            if char not in prev_positions:
                prev_positions[char] = width
            
            # Interpolate position
            current_x = prev_positions[char] + (final_x - prev_positions[char]) * ease_factor
            
            # Render the character
            render_bitmap_char(display, char, (current_x, 1), color)
        
        # Update the display
        display.show()
        
        # Sleep longer for slower animation
        time.sleep(0.01 / speed_factor)
    
    # Update previous positions for next animation
    prev_positions = final_positions.copy()

def animate_marquee(display, text, colors, offset, speed_factor=1.0):
    """
    Animate a continuous scrolling marquee effect with smooth motion
    
    Args:
        display: UnicornHATMini instance
        text: String of characters to display
        colors: List of colors corresponding to each character
        offset: Current pixel offset for the animation
        speed_factor: Speed multiplier (lower is slower)
        
    Returns:
        New offset value
    """
    width, height = display.get_shape()
    
    # Calculate the total width of the text (including inter-character spacing)
    total_width = len(text) * (CHAR_WIDTH + CHAR_SPACING) - CHAR_SPACING
    
    # Clear the display
    display.clear()
    
    # Draw each character at its offset position
    for i, char in enumerate(text):
        # Calculate the x position for this character with wrapping
        char_offset = (i * (CHAR_WIDTH + CHAR_SPACING) - offset) % total_width
        
        # When we've wrapped around, add the total width to ensure continuity
        if char_offset < 0:
            char_offset += total_width
            
        # Convert to screen position (start outside the right edge)
        x_pos = width + char_offset - total_width
        
        # Only draw if it's at least partially on screen
        if -CHAR_WIDTH < x_pos < width:
            render_bitmap_char(display, char, (x_pos, 1), colors[i])
    
    # Update the display
    display.show()
    
    # Increment and wrap the offset (slower with lower speed_factor)
    offset = (offset + 0.2 / speed_factor) % total_width
    
    # Return the new offset
    return offset

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Animated Text Display for Unicorn HAT Mini')
    
    parser.add_argument('--type', '-t', 
                        choices=['push', 'pop', 'marquee'],
                        default='push',
                        help='Animation style: push, pop, or marquee')
    
    parser.add_argument('--brightness', '-b',
                        type=float,
                        default=0.5,
                        help='Display brightness from 0.0 to 1.0')
    
    parser.add_argument('--speed', '-s',
                        type=float,
                        default=1.0,
                        help='Animation speed (lower value = slower animations)')
    
    return parser.parse_args()

def main():
    # Import math for easing functions
    import math
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize the Unicorn HAT Mini
    display = UnicornHATMini()
    display.set_brightness(args.brightness)
    clear_display(display)
    
    # Initialize text state
    char_queue = []  # List of (char, color) tuples
    marquee_offset = 0.0  # Using float for smoother motion
    animation_mode = args.type
    speed_factor = args.speed  # Animation speed factor
    
    print(f"Animated Text Display for Unicorn HAT Mini ({animation_mode} mode)")
    print(f"Animation speed: {speed_factor:.1f}x (use --speed option to adjust)")
    print("Type characters to display them. Press Ctrl+C to exit.")
    
    # For marquee mode, we need to handle animation continuously
    marquee_last_update = time.time()
    marquee_update_interval = 0.03 / speed_factor  # Using speed factor for marquee interval
    
    try:
        while True:
            # Check for keyboard input (non-blocking)
            if animation_mode == 'marquee' and char_queue:
                # For marquee mode, we need to continuously update even without input
                import select
                if select.select([sys.stdin], [], [], 0.0)[0]:
                    char = getch()
                    has_input = True
                else:
                    char = None
                    has_input = False
                    
                # Update marquee animation at regular intervals
                current_time = time.time()
                if current_time - marquee_last_update >= marquee_update_interval:
                    # Convert char_queue to strings and color lists for the marquee function
                    text = ''.join(c for c, _ in char_queue)
                    colors = [color for _, color in char_queue]
                    
                    # Update the marquee animation
                    marquee_offset = animate_marquee(display, text, colors, marquee_offset, speed_factor)
                    marquee_last_update = current_time
            else:
                # For other modes, we wait for input
                char = getch()
                has_input = True
            
            # Process input if we have it
            if has_input:
                # Check for Ctrl+C (ASCII value 3)
                if char and ord(char) == 3:
                    raise KeyboardInterrupt
                
                if char:
                    # Generate a random color for this character
                    color = get_random_color()
                    
                    # Add the character to the queue
                    char_queue.append((char, color))
                    
                    # Echo the character to the terminal with color info
                    sys.stdout.write(f"{char} [RGB: {color[0]},{color[1]},{color[2]}]\n")
                    sys.stdout.flush()
                    
                    # Animate based on the selected mode
                    if animation_mode == 'push':
                        animate_push(display, char_queue, speed_factor)
                    elif animation_mode == 'pop':
                        animate_pop(display, char_queue, speed_factor)
                    # For marquee mode, the animation is handled above
            
            # Add a small delay to prevent CPU hogging
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clear the display
        clear_display(display)
        print("\nDisplay cleared.")

if __name__ == "__main__":
    main()
