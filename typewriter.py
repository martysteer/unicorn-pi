#!/usr/bin/env python3
"""
Animated Text Display for Unicorn HAT Mini

A script that displays typed characters with various animation styles.
Each keypress is immediately displayed on the Unicorn HAT Mini.
Press Enter to clear the text buffer.

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

Press Enter to clear the buffer.
Press Ctrl+C to exit.
"""

import sys
import time
import random
import math
import argparse
import termios
import tty
import fcntl
import os
import select
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

class TextBuffer:
    """
    A simple buffer class to manage text and its rendering.
    """
    def __init__(self, max_width):
        self.chars = []  # List of (char, color) tuples
        self.max_width = max_width
        self.char_width = CHAR_WIDTH
        self.char_spacing = CHAR_SPACING
        self.char_unit = self.char_width + self.char_spacing
        self.y_position = 1  # Vertical position (fixed for simplicity)
        self.marquee_offset = 0.0
    
    def add_char(self, char, color):
        """Add a character to the buffer with a color"""
        self.chars.append((char, color))
    
    def get_text(self):
        """Get the current text as a string"""
        return ''.join(char for char, _ in self.chars)
    
    def get_max_chars_visible(self):
        """Calculate how many characters can fit on screen"""
        return (self.max_width + self.char_spacing) // self.char_unit
    
    def get_start_x(self):
        """Calculate starting X position for right-aligned text"""
        max_visible = self.get_max_chars_visible()
        visible_chars = self.chars[-max_visible:] if len(self.chars) > max_visible else self.chars
        total_width = len(visible_chars) * self.char_unit - self.char_spacing
        return self.max_width - total_width
    
    def clear(self):
        """Clear the buffer"""
        self.chars = []
        self.marquee_offset = 0.0

def get_random_color():
    """Generate a vibrant random RGB color"""
    # Use more vibrant colors by avoiding dark/low values
    r = random.randint(100, 255)
    g = random.randint(100, 255)
    b = random.randint(100, 255)
    return (r, g, b)

def set_non_blocking_input():
    """Set stdin to non-blocking mode"""
    fd = sys.stdin.fileno()
    old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)
    return fd, old_flags

def restore_input(fd, old_flags):
    """Restore stdin to original mode"""
    fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)

def setup_terminal():
    """Set terminal to raw mode for character-by-character input"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(fd)
    return fd, old_settings

def restore_terminal(fd, old_settings):
    """Restore terminal to original mode"""
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def has_input(timeout=0.0):
    """Check if input is available within timeout"""
    return sys.stdin in select.select([sys.stdin], [], [], timeout)[0]

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
                # Calculate the actual position on the display
                pixel_x = int(x_pos + x)
                pixel_y = int(y_pos + y)
                
                # Check if the pixel is within display bounds
                if 0 <= pixel_x < display.get_shape()[0] and 0 <= pixel_y < display.get_shape()[1]:
                    display.set_pixel(pixel_x, pixel_y, *color)

def clear_display(display):
    """Clear the display and show it"""
    display.clear()
    display.show()

def animate_push(display, text_buffer, speed_factor=1.0):
    """
    Animate a new character pushing in from the right
    
    Args:
        display: UnicornHATMini instance
        text_buffer: TextBuffer instance
        speed_factor: Speed multiplier (higher is faster)
    """
    max_visible = text_buffer.get_max_chars_visible()
    visible_chars = text_buffer.chars[-max_visible:] if len(text_buffer.chars) > max_visible else text_buffer.chars
    start_x = text_buffer.get_start_x()
    
    # Number of animation steps (more steps = smoother animation)
    steps = int(15 / speed_factor)
    
    # Animate the push
    for step in range(steps + 1):
        # Calculate progress factor (0.0 to 1.0)
        progress = step / steps
        
        # Clear the display
        display.clear()
        
        # Draw characters with animated positions
        for i, (char, color) in enumerate(visible_chars):
            # Calculate position with easing
            ease = 0.5 - 0.5 * math.cos(progress * math.pi)
            offset = (1.0 - ease) * text_buffer.char_unit
            
            # Calculate final x position
            x_pos = start_x + (i * text_buffer.char_unit) - offset
            
            # Only draw if at least partially on screen
            if -CHAR_WIDTH < x_pos < display.get_shape()[0]:
                render_bitmap_char(display, char, (x_pos, text_buffer.y_position), color)
        
        # Update the display
        display.show()
        
        # Short delay between frames
        time.sleep(0.01)

def animate_pop(display, text_buffer, speed_factor=1.0):
    """
    Animate characters appearing one by one
    
    Args:
        display: UnicornHATMini instance
        text_buffer: TextBuffer instance
        speed_factor: Speed multiplier (higher is faster)
    """
    max_visible = text_buffer.get_max_chars_visible()
    visible_chars = text_buffer.chars[-max_visible:] if len(text_buffer.chars) > max_visible else text_buffer.chars
    start_x = text_buffer.get_start_x()
    
    # Number of animation steps
    steps = int(15 / speed_factor)
    
    # Animate each character's appearance
    for step in range(steps + 1):
        # Calculate progress factor (0.0 to 1.0)
        progress = step / steps
        
        # Apply easing function for smoother motion
        ease = 0.5 - 0.5 * math.cos(progress * math.pi)
        
        # Clear the display
        display.clear()
        
        # Draw each character
        for i, (char, color) in enumerate(visible_chars):
            # Each character's final position
            final_x = start_x + (i * text_buffer.char_unit)
            
            # For the newly added character, animate it in from the right
            if i == len(visible_chars) - 1:
                # Start from off-screen right
                start_pos = display.get_shape()[0]
                # Calculate current position
                x_pos = start_pos + (final_x - start_pos) * ease
            else:
                # All other characters stay in place
                x_pos = final_x
            
            # Only draw if at least partially on screen
            if -CHAR_WIDTH < x_pos < display.get_shape()[0]:
                render_bitmap_char(display, char, (x_pos, text_buffer.y_position), color)
        
        # Update the display
        display.show()
        
        # Sleep for smooth animation
        time.sleep(0.01)

def update_marquee(display, text_buffer, speed_factor=1.0):
    """
    Update the marquee scroll animation
    
    Args:
        display: UnicornHATMini instance
        text_buffer: TextBuffer instance
        speed_factor: Speed multiplier (higher is faster)
    """
    # If no characters, just return
    if not text_buffer.chars:
        display.clear()
        display.show()
        return
    
    # Calculate the total width of all characters (for wrapping)
    total_width = len(text_buffer.chars) * text_buffer.char_unit
    
    # Increment marquee offset
    text_buffer.marquee_offset += 0.5 * speed_factor
    # Wrap around when needed
    if text_buffer.marquee_offset >= total_width:
        text_buffer.marquee_offset = 0.0
    
    # Clear the display
    display.clear()
    
    # Draw each character at its scrolled position
    for i, (char, color) in enumerate(text_buffer.chars):
        # Calculate base position for scrolling
        x_pos = i * text_buffer.char_unit - text_buffer.marquee_offset
        
        # Wrap around for continuous scrolling
        if x_pos < -text_buffer.char_width:
            x_pos += total_width
        
        # Only draw if at least partially on screen
        if -CHAR_WIDTH < x_pos < display.get_shape()[0]:
            render_bitmap_char(display, char, (x_pos, text_buffer.y_position), color)
    
    # Update the display
    display.show()

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
                        help='Animation speed (higher value = faster animations)')
    
    return parser.parse_args()

def main():
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize the Unicorn HAT Mini
    display = UnicornHATMini()
    width, height = display.get_shape()
    display.set_brightness(args.brightness)
    clear_display(display)
    
    # Initialize the text buffer
    text_buffer = TextBuffer(width)
    animation_mode = args.type
    speed_factor = args.speed
    
    # Initialize time tracking
    last_update_time = time.time()
    update_interval = 0.05 / speed_factor  # Base update interval
    
    print(f"Animated Text Display for Unicorn HAT Mini ({animation_mode} mode)")
    print(f"Animation speed: {speed_factor:.1f}x (use --speed option to adjust)")
    print("Type characters to display them. Press Enter to clear the buffer. Press Ctrl+C to exit.")
    
    # Setup terminal for raw input
    term_fd, old_term_settings = setup_terminal()
    
    try:
        while True:
            current_time = time.time()
            
            # Check for input (non-blocking)
            if has_input(0.0):
                char = sys.stdin.read(1)
                
                # Check for Ctrl+C
                if char and ord(char) == 3:
                    raise KeyboardInterrupt
                
                # Check for Enter key (clear buffer)
                if char and (ord(char) == 13 or ord(char) == 10):  # CR or LF
                    text_buffer.clear()
                    sys.stdout.write('\r\n')
                    sys.stdout.flush()
                    
                    # Clear display
                    clear_display(display)
                    
                    # Skip the rest of the loop
                    continue
                
                # Process other characters
                if char and ord(char) >= 32:  # Only printable characters
                    # Generate a random color
                    color = get_random_color()
                    
                    # Add character to the buffer
                    text_buffer.add_char(char, color)
                    
                    # Echo character to terminal
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    
                    # Apply animation based on mode
                    if animation_mode == 'push':
                        animate_push(display, text_buffer, speed_factor)
                        last_update_time = current_time  # Reset the timer
                    elif animation_mode == 'pop':
                        animate_pop(display, text_buffer, speed_factor)
                        last_update_time = current_time  # Reset the timer
            
            # For marquee mode, update continuously
            if animation_mode == 'marquee' and current_time - last_update_time >= update_interval:
                update_marquee(display, text_buffer, speed_factor)
                last_update_time = current_time
            
            # Sleep a tiny bit to prevent CPU hogging
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Restore terminal settings
        restore_terminal(term_fd, old_term_settings)
        
        # Clear the display
        clear_display(display)
        print("\nDisplay cleared.")

if __name__ == "__main__":
    main()