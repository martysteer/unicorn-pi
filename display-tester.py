#!/usr/bin/env python3
"""
Unicorn HAT Mini Display Tester

A simple utility to test and demonstrate the Unicorn HAT Mini display
by showing colored patterns and responding to button presses.
"""

import argparse
import time
from PIL import Image, ImageDraw
import colorsys
import sys

try:
    from unicornhatutils import UnicornHATMini, display_info_message, clear_display
except ImportError:
    print("Error: Could not import from unicornhatutils. Make sure unicornhatutils.py is in the same directory.")
    exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Display tester for Unicorn HAT Mini')
    parser.add_argument('--pattern', type=str, default='solid',
                        choices=['solid', 'rainbow', 'checkerboard', 'gradient'],
                        help='Pattern to display (default: solid)')
    parser.add_argument('--color', type=str, default='FF52DA',
                        help='Color for solid pattern in hex format (default: FF52DA)')
    parser.add_argument('--brightness', type=float, default=0.5,
                        help='Display brightness from 0.0 to 1.0 (default: 0.5)')
    return parser.parse_args()


def hex_to_rgb(hex_color):
    # Remove the '#' if it exists
    hex_color = hex_color.lstrip('#')
    
    # Convert the hex color to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def draw_solid(display, color):
    """Fill the display with a solid color."""
    r, g, b = color
    display.set_all(r, g, b)
    display.show()


def draw_rainbow(display, offset=0):
    """Draw a rainbow pattern."""
    width, height = display.get_shape()
    for y in range(height):
        for x in range(width):
            hue = (x + y + offset) / float(width + height)
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            display.set_pixel(x, y, r, g, b)
    display.show()


def draw_checkerboard(display, color1=(255, 255, 255), color2=(0, 0, 0)):
    """Draw a checkerboard pattern."""
    width, height = display.get_shape()
    for y in range(height):
        for x in range(width):
            if (x + y) % 2 == 0:
                display.set_pixel(x, y, *color1)
            else:
                display.set_pixel(x, y, *color2)
    display.show()


def draw_gradient(display, start_color=(255, 0, 0), end_color=(0, 0, 255)):
    """Draw a gradient from left to right."""
    width, height = display.get_shape()
    r1, g1, b1 = start_color
    r2, g2, b2 = end_color
    
    for x in range(width):
        # Calculate color for this column
        ratio = x / float(width - 1)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        # Fill the column with this color
        for y in range(height):
            display.set_pixel(x, y, r, g, b)
    
    display.show()


def button_callback(button):
    """Handle button press events."""
    button_names = {
        UnicornHATMini.BUTTON_A: "A",
        UnicornHATMini.BUTTON_B: "B",
        UnicornHATMini.BUTTON_X: "X",
        UnicornHATMini.BUTTON_Y: "Y"
    }
    print(f"Button {button_names.get(button, button)} pressed!")


def main():
    args = parse_arguments()
    
    # Parse the color argument for solid pattern
    try:
        color = hex_to_rgb(args.color)
    except ValueError:
        print(f"Error: Color '{args.color}' should be a valid hex color code (e.g., FF52DA)")
        return
    
    # Initialize the Unicorn HAT Mini
    display = UnicornHATMini()
    
    # Set brightness
    brightness = max(0.1, min(1.0, args.brightness))
    display.set_brightness(brightness)
    
    # Register button callback
    display.on_button_pressed(button_callback)
    
    # Display a startup message
    display_info_message(display, "Unicorn HAT", "Tester")
    time.sleep(1)
    
    # Select and draw the requested pattern
    pattern = args.pattern.lower()
    
    print(f"Displaying '{pattern}' pattern")
    print("Press A, B, X, Y buttons to see events")
    print("Press Ctrl+C to exit")
    
    try:
        # Initial pattern draw
        if pattern == 'solid':
            draw_solid(display, color)
        elif pattern == 'rainbow':
            offset = 0
        elif pattern == 'checkerboard':
            draw_checkerboard(display)
        elif pattern == 'gradient':
            draw_gradient(display)
        
        # Main loop for animations and button checking
        while True:
            if pattern == 'rainbow':
                draw_rainbow(display, offset)
                offset = (offset + 1) % 64
            
            # Process events
            display.process_events()
            
            # Sleep to control animation speed and prevent CPU hogging
            time.sleep(0.05)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clean up and clear the display
        clear_display(display)
        print("Display cleared")


if __name__ == "__main__":
    main()
