#!/usr/bin/env python3
"""
Interactive Rectangle Demo for Unicorn HAT Mini

A demo application that displays a colorful rectangle border that you can manipulate
using the Unicorn HAT Mini's buttons:

- Button A: Move the top edge down (shrink from top)
- Button B: Move the left edge right (shrink from left)
- Button X: Move the bottom edge up (shrink from bottom)
- Button Y: Move the right edge left (shrink from right)

Press and hold any button to reset the rectangle to full size.
"""

import time
import argparse
import colorsys
import sys

try:
    # Try to import from the unicornhatutils wrapper first (which works on macOS too)
    from unicornhatutils import UnicornHATMini, display_info_message, clear_display
except ImportError:
    try:
        # Fall back to the direct library (Raspberry Pi only)
        from unicornhatmini import UnicornHATMini
        
        # Simple implementation of display_info_message for fallback
        def display_info_message(display, message, submessage=""):
            display.clear()
            # No fancy text, just set some pixels as a visual indicator
            for x in range(display.get_shape()[0]):
                display.set_pixel(x, 0, 255, 255, 255)
                display.set_pixel(x, display.get_shape()[1]-1, 255, 255, 255)
            display.show()
            time.sleep(1)
            
        def clear_display(display):
            display.clear()
            display.show()
    except ImportError:
        print("Error: Could not import UnicornHATMini. Please make sure the library is installed.")
        print("For Raspberry Pi: sudo pip3 install unicornhatmini")
        print("For development on macOS: Place unicornhatutils.py and proxyunicornhatmini.py in the same directory.")
        exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Interactive Rectangle Demo for Unicorn HAT Mini')
    parser.add_argument('--brightness', '-b', type=float, default=0.5,
                       help='Display brightness from 0.0 to 1.0 (default: 0.5)')
    parser.add_argument('--speed', '-s', type=float, default=0.05,
                       help='Animation speed (lower is faster) (default: 0.05)')
    return parser.parse_args()


def get_rainbow_color(offset):
    """Get a color from the rainbow spectrum."""
    hue = (time.time() / 5.0 + offset) % 1.0
    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
    return r, g, b


def draw_rectangle(display, top, left, bottom, right, width, height):
    """Draw a colorful rectangle border on the display."""
    display.clear()
    
    # Make sure the rectangle is valid
    top = max(0, min(top, height - 1))
    left = max(0, min(left, width - 1))
    bottom = max(top, min(bottom, height - 1))
    right = max(left, min(right, width - 1))
    
    # Draw top edge
    for x in range(left, right + 1):
        color = get_rainbow_color(x / float(width))
        display.set_pixel(x, top, *color)
    
    # Draw bottom edge
    for x in range(left, right + 1):
        color = get_rainbow_color(x / float(width) + 0.25)
        display.set_pixel(x, bottom, *color)
    
    # Draw left edge
    for y in range(top + 1, bottom):
        color = get_rainbow_color(y / float(height) + 0.5)
        display.set_pixel(left, y, *color)
    
    # Draw right edge
    for y in range(top + 1, bottom):
        color = get_rainbow_color(y / float(height) + 0.75)
        display.set_pixel(right, y, *color)
    
    display.show()


def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize Unicorn HAT Mini
    display = UnicornHATMini()
    width, height = display.get_shape()
    
    # Set brightness
    brightness = max(0.1, min(1.0, args.brightness))
    display.set_brightness(brightness)
    
    # Display startup message
    display_info_message(display, "Rectangle", "Demo")
    time.sleep(1)
    
    # Rectangle coordinates (initially full screen)
    top = 0
    left = 0
    bottom = height - 1
    right = width - 1
    
    # Button press tracking
    button_press_times = {
        display.BUTTON_A: 0,
        display.BUTTON_B: 0,
        display.BUTTON_X: 0,
        display.BUTTON_Y: 0
    }
    
    try:
        # Main loop
        while True:
            # Check for button presses
            for button, pin in [
                ("A", display.BUTTON_A),
                ("B", display.BUTTON_B),
                ("X", display.BUTTON_X),
                ("Y", display.BUTTON_Y)
            ]:
                # Read current button state
                is_pressed = display.read_button(pin)
                
                # Handle long press (for reset)
                if is_pressed:
                    if button_press_times[pin] == 0:
                        button_press_times[pin] = time.time()
                    elif time.time() - button_press_times[pin] > 1.0:
                        # Long press detected - reset rectangle
                        print(f"Button {button} long press - resetting rectangle")
                        top = 0
                        left = 0
                        bottom = height - 1
                        right = width - 1
                        button_press_times[pin] = time.time()  # Reset timer to prevent multiple triggers
                else:
                    # Handle short press (edge movement)
                    if button_press_times[pin] > 0:
                        press_duration = time.time() - button_press_times[pin]
                        if press_duration < 1.0:  # Short press
                            # Modify rectangle based on button
                            if pin == display.BUTTON_A and top < bottom:
                                top += 1
                                print(f"Button {button} pressed - moving top edge down to {top}")
                            elif pin == display.BUTTON_B and left < right:
                                left += 1
                                print(f"Button {button} pressed - moving left edge right to {left}")
                            elif pin == display.BUTTON_X and bottom > top:
                                bottom -= 1
                                print(f"Button {button} pressed - moving bottom edge up to {bottom}")
                            elif pin == display.BUTTON_Y and right > left:
                                right -= 1
                                print(f"Button {button} pressed - moving right edge left to {right}")
                        # Reset button timer
                        button_press_times[pin] = 0
            
            # Draw the current rectangle state
            draw_rectangle(display, top, left, bottom, right, width, height)
            
            # Process events (needed for proxy implementation)
            if hasattr(display, 'process_events'):
                display.process_events()
            
            # Sleep to control animation speed
            time.sleep(args.speed)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clean up
        clear_display(display)
        print("Display cleared")


if __name__ == "__main__":
    main()
