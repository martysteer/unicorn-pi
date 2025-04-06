#!/usr/bin/env python3
"""
Rainbow Text Scroller for Unicorn HAT Mini

A script that scrolls multicolored text with interactive button controls:
- Button A: Toggle between slow, medium, and fast scroll speeds
- Button B: Cycle through different color animation effects
- Button X: Move text baseline down
- Button Y: Move text baseline up

Usage: python rainbow_text_scroller.py --text "Your text here"
"""

import argparse
import time
import math
import colorsys
import random
import sys
from PIL import Image, ImageDraw, ImageFont

# Try to import HAT Mini library with cross-platform support
try:
    from unicornhatutils import UnicornHATMini, display_info_message, clear_display
except ImportError:
    try:
        from unicornhatmini import UnicornHATMini
        
        # Simple implementations if we're on actual hardware
        def display_info_message(display, message, submessage=""):
            display.clear()
            display.show()
            time.sleep(0.5)
            
        def clear_display(display):
            display.clear()
            display.show()
    except ImportError:
        print("Error: Could not import UnicornHATMini library.")
        print("Please install it with: sudo pip3 install unicornhatmini")
        print("Or place unicornhatutils.py in the same directory.")
        sys.exit(1)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Multicolor Text Scroller for Unicorn HAT Mini')
    
    parser.add_argument('--text', type=str, default="Hello World!",
                       help='Text to scroll across the display')
    
    parser.add_argument('--brightness', '-b', type=float, default=0.5,
                       help='Display brightness (0.0-1.0)')
    
    parser.add_argument('--font', type=str, default=None,
                       help='Path to TTF font file (default: built-in font)')
    
    parser.add_argument('--speed', type=str, default='medium',
                       choices=['slow', 'medium', 'fast'],
                       help='Initial scroll speed')
    
    return parser.parse_args()


class RainbowTextScroller:
    """Controls the scrolling text display and button interactions."""
    
    def __init__(self, display, text, font_path=None, initial_speed='medium'):
        """Initialize the rainbow text scroller."""
        self.display = display
        self.width, self.height = display.get_shape()
        self.text = text
        self.font_path = font_path
        
        # Scrolling parameters
        self.speed_settings = {
            'slow': 0.1,    # pixels per frame
            'medium': 0.2,  # pixels per frame
            'fast': 0.4     # pixels per frame
        }
        self.current_speed = initial_speed
        self.scroll_x = self.width  # Start off-screen to the right
        self.scroll_step = self.speed_settings[self.current_speed]
        
        # Text baseline position (vertical centering)
        self.baseline_y = (self.height - 5) // 2  # Default to vertically centered
        
        # Color effects
        self.color_modes = ['static_rainbow', 'wave', 'pulse', 'random_flash']
        self.current_color_mode = 0  # Start with static rainbow
        self.color_time = 0          # For time-based effects
        self.flash_countdown = 0     # For random flash effect
        
        # Set up text rendering
        self.setup_text()
        
        # Button tracking
        self.prev_button_states = {
            display.BUTTON_A: False,
            display.BUTTON_B: False,
            display.BUTTON_X: False,
            display.BUTTON_Y: False
        }
    
    def setup_text(self):
        """Set up the text image for scrolling."""
        # Load a font
        try:
            if self.font_path:
                self.font = ImageFont.truetype(self.font_path, 8)
            else:
                # Try to load a system font, fall back to default if not available
                try:
                    self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
                except IOError:
                    self.font = ImageFont.load_default()
        except Exception as e:
            print(f"Font error: {e}")
            self.font = ImageFont.load_default()
            
        # Measure the size of our text
        try:
            # For newer PIL versions
            left, top, right, bottom = self.font.getbbox(self.text)
            self.text_width = right - left
            self.text_height = bottom - top
        except AttributeError:
            # Fallback for older PIL versions
            self.text_width, self.text_height = self.font.getsize(self.text)
            
        print(f"Text dimensions: {self.text_width}x{self.text_height}")
        
        # Create a new PIL image big enough to fit the text and display width
        # This will be our scrolling buffer
        buffer_width = self.text_width + (2 * self.width)
        self.text_image = Image.new("RGB", (buffer_width, self.height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.text_image)
    
    def change_speed(self):
        """Cycle through scroll speeds: slow -> medium -> fast -> slow..."""
        speeds = list(self.speed_settings.keys())
        current_idx = speeds.index(self.current_speed)
        next_idx = (current_idx + 1) % len(speeds)
        self.current_speed = speeds[next_idx]
        self.scroll_step = self.speed_settings[self.current_speed]
        print(f"Speed changed to {self.current_speed} ({self.scroll_step} px/frame)")
    
    def change_color_mode(self):
        """Cycle through different color animation effects."""
        self.current_color_mode = (self.current_color_mode + 1) % len(self.color_modes)
        mode_name = self.color_modes[self.current_color_mode]
        print(f"Color mode changed to: {mode_name}")
        
        # Reset any mode-specific parameters
        if mode_name == 'random_flash':
            self.flash_countdown = 5  # Trigger an immediate flash
    
    def move_baseline(self, direction):
        """Move the text baseline up or down."""
        # direction: 1 for up, -1 for down
        new_y = self.baseline_y + direction
        
        # Keep within reasonable bounds
        if 0 <= new_y <= self.height - 1:
            self.baseline_y = new_y
            print(f"Baseline position: {self.baseline_y}")
    
    def handle_buttons(self):
        """Check for button presses and handle accordingly."""
        buttons = {
            self.display.BUTTON_A: self.change_speed,
            self.display.BUTTON_B: self.change_color_mode,
            self.display.BUTTON_X: lambda: self.move_baseline(1),   # Down (increase Y)
            self.display.BUTTON_Y: lambda: self.move_baseline(-1),  # Up (decrease Y)
        }
        
        for button, action in buttons.items():
            # Get previous and current button state
            prev_state = self.prev_button_states.get(button, False)
            curr_state = self.display.read_button(button)
            
            # Update previous state for next time
            self.prev_button_states[button] = curr_state
            
            # Check for a button press (transition from not pressed to pressed)
            if curr_state and not prev_state:
                action()
    
    def get_pixel_color(self, x, text_x, y):
        """Determine the color for a specific pixel based on the current color mode."""
        # Get a normalized position of this character in the text (0.0 to 1.0)
        char_position = text_x / self.text_width
        
        # Current time for animations
        t = time.time()
        self.color_time = t
        
        # Check if this pixel is part of the text or background
        # For simplicity, we use black for background and apply color only to non-black pixels
        pixel = self.text_image.getpixel((x, y))
        if pixel == (0, 0, 0):
            return 0, 0, 0  # Background stays black
        
        # Different coloring modes
        mode = self.color_modes[self.current_color_mode]
        
        if mode == 'static_rainbow':
            # Each letter has a different fixed color
            hue = char_position
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            
        elif mode == 'wave':
            # Rainbow wave flowing through the text
            hue = (char_position + t * 0.2) % 1.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            
        elif mode == 'pulse':
            # All text pulses through colors together
            pulse_speed = 0.3  # Color cycles per second
            hue = (t * pulse_speed) % 1.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            
        elif mode == 'random_flash':
            # Random letters flash to different colors
            # We'll use the standard rainbow, but occasionally change some letters
            
            # First, calculate the base color like in static_rainbow
            hue = char_position
            
            # Decrement flash countdown and check if we should flash
            self.flash_countdown -= 1
            if self.flash_countdown <= 0:
                # Reset the countdown to a random value for next flash
                self.flash_countdown = random.randint(5, 15)
                
                # Add some randomness to the hue for a flash effect
                # But only for some characters
                if random.random() < 0.3:  # 30% chance per letter
                    hue = random.random()  # Completely random color
            
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
        
        else:
            # Fallback to static rainbow
            hue = char_position
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
        
        return r, g, b
    
    def update(self):
        """Update the display with the current frame of scrolling text."""
        # Clear the text image
        self.draw.rectangle((0, 0, self.text_image.width, self.text_image.height), fill=(0, 0, 0))
        
        # Draw the text at the baseline position
        # Get vertical position based on baseline and text height
        y_position = self.baseline_y - self.text_height // 2
        self.draw.text((self.width, y_position), self.text, font=self.font, fill=(255, 255, 255))
        
        # Clear the display
        self.display.clear()
        
        # Calculate the visible window of the scrolling text
        # This is based on current scroll position
        visible_x = int(self.scroll_x)
        
        # Draw each visible pixel
        for y in range(self.height):
            for x in range(self.width):
                # Get the corresponding position in the text image
                text_x = x + visible_x
                
                # Skip if out of bounds
                if text_x < 0 or text_x >= self.text_image.width:
                    continue
                
                # Apply the current color effect
                r, g, b = self.get_pixel_color(text_x, text_x - self.width, y)
                
                # Set the pixel on the display
                self.display.set_pixel(x, y, r, g, b)
        
        # Update the display
        self.display.show()
        
        # Update scroll position for next frame
        self.scroll_x -= self.scroll_step
        
        # If the text has scrolled completely off the left edge, reset to start
        if self.scroll_x < -self.text_width:
            self.scroll_x = self.width
    
    def run(self):
        """Run the main loop of the text scroller."""
        try:
            # Show welcome message
            display_info_message(self.display, "Rainbow", "Text Scroller")
            time.sleep(1)
            
            while True:
                # Handle button presses
                self.handle_buttons()
                
                # Update the display
                self.update()
                
                # Process events (needed for proxy implementation)
                if hasattr(self.display, 'process_events'):
                    self.display.process_events()
                
                # Short delay to control frame rate
                time.sleep(0.03)  # ~30 FPS
                
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            # Clean up
            clear_display(self.display)
            print("Display cleared")


def main():
    """Main function to run the rainbow text scroller."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize the display
    display = UnicornHATMini()
    
    # Set brightness
    brightness = max(0.1, min(1.0, args.brightness))
    display.set_brightness(brightness)
    
    # Create and run the text scroller
    scroller = RainbowTextScroller(
        display=display,
        text=args.text,
        font_path=args.font,
        initial_speed=args.speed
    )
    
    scroller.run()


if __name__ == "__main__":
    main()
