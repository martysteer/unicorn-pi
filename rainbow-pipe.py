#!/usr/bin/env python3
"""
Rainbow Text Pipe for Unicorn HAT Mini

A script that displays scrolling rainbow text and can receive new text
from stdin (either typed directly or piped from another process).

Examples:
    # Run with default message:
    python rainbow-pipe.py
    
    # Pipe output from another command:
    echo "Hello from pipe" | python rainbow-pipe.py
    
    # Use with tee to display command output while also sending to file:
    ls -la | tee output.txt | python rainbow-pipe.py
    
    # Interactive use (type and press Enter to add text):
    python rainbow-pipe.py

Button controls:
- Button A: Toggle between slow, medium, and fast scroll speeds
- Button B: Cycle through different color animation effects
- Button X: Move text baseline down
- Button Y: Move text baseline up
"""

import argparse
import time
import sys
import os
import math
import colorsys
import random
import select
import queue
import threading
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
    parser = argparse.ArgumentParser(description='Rainbow Text Pipe for Unicorn HAT Mini')
    
    parser.add_argument('--initial-text', type=str, default="Unicorn HAT Mini > ",
                       help='Initial text to display (default: "Unicorn HAT Mini > ")')
    
    parser.add_argument('--brightness', '-b', type=float, default=0.5,
                       help='Display brightness (0.0-1.0)')
    
    parser.add_argument('--font', type=str, default=None,
                       help='Path to TTF font file (default: built-in font)')
    
    parser.add_argument('--speed', type=str, default='medium',
                       choices=['slow', 'medium', 'fast'],
                       help='Initial scroll speed')
    
    parser.add_argument('--max-length', type=int, default=256,
                       help='Maximum number of characters to keep in buffer')
    
    parser.add_argument('--separator', type=str, default=" | ",
                       help='Separator between input segments')
    
    parser.add_argument('--no-stdin', action='store_true',
                       help='Disable stdin input (only show initial text)')
    
    parser.add_argument('--system-font', action='store_true',
                       help='Use system font instead of the custom pixel font')
    
    return parser.parse_args()


class StdinReader(threading.Thread):
    """Thread for reading from stdin without blocking the main loop."""
    
    def __init__(self, input_queue, stop_event):
        """Initialize the stdin reader thread.
        
        Args:
            input_queue: Queue to put input lines into
            stop_event: Threading event to signal when to stop
        """
        super().__init__()
        self.input_queue = input_queue
        self.stop_event = stop_event
        self.daemon = True  # Thread will exit when main program exits
    
    def run(self):
        """Run the thread, reading from stdin and putting lines in the queue."""
        # Check if stdin is a terminal or pipe
        is_pipe = not os.isatty(sys.stdin.fileno())
        
        # Set stdin to non-blocking mode
        if not is_pipe:
            print("Interactive mode: Type text and press Enter to display")
            print("Press Ctrl+C to exit")
        
        try:
            while not self.stop_event.is_set():
                # Check if there's data available on stdin
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                
                if r:
                    line = sys.stdin.readline().strip()
                    if line:  # Only process non-empty lines
                        self.input_queue.put(line)
                
                # If reading from a pipe and we've reached EOF, exit
                if is_pipe and not r:
                    # Check if we've reached EOF
                    if sys.stdin.closed or not select.select([sys.stdin], [], [], 0):
                        break
                
                # Short sleep to prevent CPU hogging
                time.sleep(0.05)
        
        except (KeyboardInterrupt, EOFError):
            # Handle keyboard interrupt or EOF gracefully
            self.stop_event.set()


class CustomPixelFont:
    """A custom pixel font for rendering text on small displays."""
    
    def __init__(self):
        """Initialize the custom pixel font."""
        self.char_width = 3  # Width of each character in pixels
        self.char_height = 5  # Height of each character in pixels
        self.char_spacing = 1  # Spacing between characters
        self.bitmap_font = create_pixel_bitmap_font()
    
    def getbbox(self, text):
        """Get the bounding box of text for PIL compatibility.
        
        Args:
            text: The text to measure
            
        Returns:
            Tuple of (left, top, right, bottom)
        """
        # Calculate the width of the text
        width = 0
        for char in text:
            if char.upper() in self.bitmap_font:
                width += self.char_width + self.char_spacing
        
        # Remove the last character spacing if there's text
        if width > 0:
            width -= self.char_spacing
            
        # Return bounding box (left, top, right, bottom)
        return (0, 0, width, self.char_height)
    
    def getsize(self, text):
        """Get the size of text for PIL compatibility.
        
        Args:
            text: The text to measure
            
        Returns:
            Tuple of (width, height)
        """
        # Use getbbox and convert to size
        left, top, right, bottom = self.getbbox(text)
        return (right - left, bottom - top)
    
    def render_text(self, draw, text, position, color=(255, 255, 255)):
        """Render text at the specified position.
        
        Args:
            draw: PIL ImageDraw object
            text: Text to render
            position: (x, y) position to draw at
            color: Color to use for the text
        """
        x, y = position
        
        # Convert text to uppercase for simplicity
        text = text.upper()
        
        # Draw each character
        for char in text:
            if char in self.bitmap_font:
                # Get the bitmap for this character
                bitmap = self.bitmap_font[char]
                
                # Draw each pixel of the character
                for cy in range(self.char_height):
                    for cx in range(self.char_width):
                        if cy < len(bitmap) and cx < len(bitmap[cy]) and bitmap[cy][cx] == 1:
                            draw.point((x + cx, y + cy), fill=color)
                
                # Move to the next character position
                x += self.char_width + self.char_spacing
            else:
                # Skip unknown characters
                x += self.char_width + self.char_spacing

class RainbowTextPipe:
    """Controls the scrolling text display and handles input from stdin."""
    
    def __init__(self, display, initial_text, font_path=None, initial_speed='medium',
                 max_length=256, separator=" | ", use_stdin=True):
        """Initialize the rainbow text pipe."""
        self.display = display
        self.width, self.height = display.get_shape()
        self.text = initial_text
        self.font_path = font_path
        self.max_length = max_length
        self.separator = separator
        self.use_stdin = use_stdin
        self.scroll_x = 0
        self.use_custom_pixel_font = True  # Set to True to use the custom pixel font
        
        # Scrolling parameters
        self.speed_settings = {
            'slow': 0.1,    # pixels per frame
            'medium': 0.2,  # pixels per frame
            'fast': 0.4     # pixels per frame
        }
        self.current_speed = initial_speed
        self.scroll_step = self.speed_settings[self.current_speed]
        
        # Add a gap between repeated scrolls for a smooth marquee effect
        self.gap_width = self.width  # One screen width gap
        
        # Text baseline position (vertical centering)
        self.baseline_y = (self.height // 2)  # Default to vertically centered
        
        # Color effects
        self.color_modes = ['static_rainbow', 'wave', 'pulse', 'random_flash']
        self.current_color_mode = 0  # Start with static rainbow
        self.color_time = 0          # For time-based effects
        self.flash_countdown = 0     # For random flash effect
        
        # Set up text rendering
        self.setup_font()
        
        # Set up input handling
        self.input_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Only start stdin reader if enabled
        if use_stdin:
            self.stdin_reader = StdinReader(self.input_queue, self.stop_event)
            self.stdin_reader.start()
        
        # When the image needs to be recreated
        self.need_update_image = True
        
        # Button tracking
        self.prev_button_states = {
            display.BUTTON_A: False,
            display.BUTTON_B: False,
            display.BUTTON_X: False,
            display.BUTTON_Y: False
        }
    
    def setup_font(self):
        """Set up the font for text rendering."""
        # Check if we should use the custom pixel font
        if self.use_custom_pixel_font:
            print("Using custom pixel font")
            self.font = CustomPixelFont()
        else:
            # Load a font
            try:
                if self.font_path:
                    self.font = ImageFont.truetype(self.font_path, 8)
                else:
                    # Try to load a pixel font, with fallbacks for different systems
                    font_paths = [
                        # Common pixel fonts on Linux
                        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
                        # Custom smaller pixel font size
                        "/usr/share/fonts/truetype/piboto/PibotoLt-Regular.ttf",
                        # Try Raspberry Pi specific fonts
                        "/usr/share/fonts/truetype/piboto/Piboto-Regular.ttf",
                        # Fall back to smaller DejaVu 
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                    ]
                    
                    for path in font_paths:
                        try:
                            # Use a smaller font size for cleaner pixel display
                            self.font = ImageFont.truetype(path, 6)
                            print(f"Using font: {path}")
                            break
                        except IOError:
                            continue
                    else:
                        # If no font was loaded, load a clean custom pixel font
                        try:
                            # For newer PIL versions - load default but with smaller size
                            self.font = ImageFont.load_default().font_variant(size=6)
                        except (AttributeError, TypeError):
                            self.font = ImageFont.load_default()
            except Exception as e:
                print(f"Font error: {e}")
                try:
                    # For newer PIL versions - load default but with smaller size
                    self.font = ImageFont.load_default().font_variant(size=6)
                except (AttributeError, TypeError):
                    self.font = ImageFont.load_default()
        
        # Create initial text image
        self.update_text_image()
    
    def update_text_image(self):
        """Update the text image with the current text."""
        # Measure the size of our text
        try:
            if isinstance(self.font, CustomPixelFont):
                # Use our custom pixel font methods
                left, top, right, bottom = self.font.getbbox(self.text)
                self.text_width = right - left
                self.text_height = bottom - top
            else:
                # For PIL fonts
                try:
                    # For newer PIL versions
                    left, top, right, bottom = self.font.getbbox(self.text)
                    self.text_width = right - left
                    self.text_height = bottom - top
                except AttributeError:
                    # Fallback for older PIL versions
                    self.text_width, self.text_height = self.font.getsize(self.text)
        except Exception as e:
            print(f"Error measuring text: {e}")
            # Fallback values
            self.text_width = len(self.text) * 5
            self.text_height = 5
        
        # Create a buffer that's just the size needed for the text
        self.text_image = Image.new("RGB", (max(self.text_width, 1), self.height), (0, 0, 0))
        draw = ImageDraw.Draw(self.text_image)
        
        # Draw the text in the buffer
        y_position = self.baseline_y - self.text_height // 2
        
        if isinstance(self.font, CustomPixelFont):
            # Use our custom pixel font renderer
            self.font.render_text(draw, self.text, (0, y_position), (255, 255, 255))
        else:
            # Use PIL's text rendering with pixel-perfect mode
            draw.fontmode = "1"  # Use "1" instead of "L" for binary font mode (no antialiasing)
            draw.text((0, y_position), self.text, font=self.font, fill=(255, 255, 255))
        
        # Reset scroll position if we're already at the beginning
        if self.scroll_x <= 0:
            self.scroll_x = self.width
        
        # Mark that we've updated the image
        self.need_update_image = False
    
    def add_text(self, new_text):
        """Add new text to the display buffer."""
        if new_text:
            # If the text is getting too long, trim from the beginning
            if len(self.text) + len(self.separator) + len(new_text) > self.max_length:
                # Remove enough characters to fit the new text
                overflow = len(self.text) + len(self.separator) + len(new_text) - self.max_length
                self.text = self.text[overflow + 10:]  # Remove a bit extra to avoid constant trimming
            
            # Add separator if there's already text
            if self.text:
                self.text += self.separator
            
            # Add the new text
            self.text += new_text
            
            # Mark that we need to update the image
            self.need_update_image = True
            
            print(f"Added text: {new_text}")
    
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
        # direction: 1 for down, -1 for up
        new_y = self.baseline_y + direction
        
        # Keep within reasonable bounds
        if 0 <= new_y <= self.height - 1:
            self.baseline_y = new_y
            print(f"Baseline position: {self.baseline_y}")
            self.need_update_image = True
    
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
        char_position = text_x / max(self.text_width, 1)  # Avoid division by zero
        
        # Current time for animations
        t = time.time()
        self.color_time = t
        
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
    
    def update_display(self):
        """Update the display with the current frame of scrolling text."""
        # Check if we need to update the text image
        if self.need_update_image:
            self.update_text_image()
        
        # Clear the display
        self.display.clear()
        
        # Update the scroll position
        self.scroll_x -= self.scroll_step
        
        # If the text has completely scrolled off the left edge (plus gap), reset
        if self.scroll_x < -self.text_width - self.gap_width:
            self.scroll_x = self.width  # Reset to start off-screen to the right
        
        # Draw the text onto the display
        for y in range(self.height):
            for x in range(self.width):
                # Calculate position in the text image
                text_x = x - int(self.scroll_x)
                
                # Check if this pixel is within the text bounds
                if 0 <= text_x < self.text_width:
                    # Get pixel from text image
                    pixel = self.text_image.getpixel((text_x, y))
                    
                    # Apply color effects to non-background pixels
                    if pixel != (0, 0, 0):
                        # Get color
                        r, g, b = self.get_pixel_color(x, text_x, y)
                        
                        # Set pixel
                        self.display.set_pixel(x, y, r, g, b)
        
        # Update the display
        self.display.show()
    
    def check_input(self):
        """Check for new input from stdin."""
        if not self.use_stdin:
            return
            
        # Check if there's anything in the input queue
        try:
            while True:  # Process all available input
                new_input = self.input_queue.get_nowait()
                self.add_text(new_input)
                self.input_queue.task_done()
        except queue.Empty:
            pass  # No more input
    
    def run(self):
        """Run the main loop of the text pipe."""
        try:
            # Show welcome message
            display_info_message(self.display, "Rainbow", "Text Pipe")
            time.sleep(1)
            
            while not self.stop_event.is_set():
                # Check for new input
                self.check_input()
                
                # Handle button presses
                self.handle_buttons()
                
                # Update the display
                self.update_display()
                
                # Process events (needed for proxy implementation)
                if hasattr(self.display, 'process_events'):
                    self.display.process_events()
                
                # Short delay to control frame rate
                time.sleep(0.03)  # ~30 FPS
                
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            # Signal the stdin reader to stop
            self.stop_event.set()
            
            # Clean up
            clear_display(self.display)
            print("Display cleared")


def create_pixel_bitmap_font():
    """Create a basic 5x3 pixel bitmap font that works well on small displays.
    
    Returns:
        A dictionary mapping characters to their bitmap representations.
    """
    # Define a minimal 5x3 pixel font (height x width)
    # 1 means pixel on, 0 means pixel off
    font = {
        'A': [
            [0, 1, 0],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1]
        ],
        'B': [
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 0]
        ],
        'C': [
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [0, 1, 1]
        ],
        'D': [
            [1, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 0]
        ],
        'E': [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 0],
            [1, 0, 0],
            [1, 1, 1]
        ],
        'F': [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 0],
            [1, 0, 0],
            [1, 0, 0]
        ],
        'G': [
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 1]
        ],
        'H': [
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1]
        ],
        'I': [
            [1, 1, 1],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 1]
        ],
        'J': [
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1],
            [1, 0, 1],
            [0, 1, 0]
        ],
        'K': [
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [1, 0, 1]
        ],
        'L': [
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 1, 1]
        ],
        'M': [
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1]
        ],
        'N': [
            [1, 0, 1],
            [1, 1, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1]
        ],
        'O': [
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0]
        ],
        'P': [
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 0],
            [1, 0, 0]
        ],
        'Q': [
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 1]
        ],
        'R': [
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [1, 0, 1]
        ],
        'S': [
            [0, 1, 1],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0]
        ],
        'T': [
            [1, 1, 1],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0]
        ],
        'U': [
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0]
        ],
        'V': [
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0],
            [0, 1, 0]
        ],
        'W': [
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1]
        ],
        'X': [
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1]
        ],
        'Y': [
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0]
        ],
        'Z': [
            [1, 1, 1],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
            [1, 1, 1]
        ],
        '0': [
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0]
        ],
        '1': [
            [0, 1, 0],
            [1, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 1]
        ],
        '2': [
            [1, 1, 0],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
            [1, 1, 1]
        ],
        '3': [
            [1, 1, 0],
            [0, 0, 1],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0]
        ],
        '4': [
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [0, 0, 1]
        ],
        '5': [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 0],
            [0, 0, 1],
            [1, 1, 0]
        ],
        '6': [
            [0, 1, 1],
            [1, 0, 0],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ],
        '7': [
            [1, 1, 1],
            [0, 0, 1],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0]
        ],
        '8': [
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ],
        '9': [
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
            [0, 0, 1],
            [0, 1, 0]
        ],
        ' ': [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ],
        '.': [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 1, 0]
        ],
        ',': [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 1, 0],
            [1, 0, 0]
        ],
        '!': [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
            [0, 1, 0]
        ],
        '?': [
            [1, 1, 0],
            [0, 0, 1],
            [0, 1, 0],
            [0, 0, 0],
            [0, 1, 0]
        ],
        ':': [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0]
        ],
        ';': [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
            [0, 1, 0],
            [1, 0, 0]
        ],
        '-': [
            [0, 0, 0],
            [0, 0, 0],
            [1, 1, 1],
            [0, 0, 0],
            [0, 0, 0]
        ],
        '+': [
            [0, 0, 0],
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
            [0, 0, 0]
        ],
        '*': [
            [0, 0, 0],
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
            [0, 0, 0]
        ],
        '/': [
            [0, 0, 1],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
            [1, 0, 0]
        ],
        '\\': [
            [1, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 1]
        ],
        '_': [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            [1, 1, 1]
        ],
        '=': [
            [0, 0, 0],
            [1, 1, 1],
            [0, 0, 0],
            [1, 1, 1],
            [0, 0, 0]
        ],
        '(': [
            [0, 1, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [0, 1, 0]
        ],
        ')': [
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1],
            [0, 1, 0]
        ],
        '[': [
            [1, 1, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 1, 0]
        ],
        ']': [
            [0, 1, 1],
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1],
            [0, 1, 1]
        ],
        '{': [
            [0, 1, 1],
            [0, 1, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 1, 1]
        ],
        '}': [
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0, 1, 0],
            [1, 1, 0]
        ],
        '<': [
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ],
        '>': [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0]
        ],
        '|': [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0]
        ],
        '^': [
            [0, 1, 0],
            [1, 0, 1],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ],
        '&': [
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 1]
        ],
        '@': [
            [0, 1, 0],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 0],
            [0, 1, 1]
        ],
        '#': [
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1]
        ],
        '%': [
            [1, 0, 1],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
            [1, 0, 1]
        ],
        '~': [
            [0, 0, 0],
            [0, 1, 0],
            [1, 0, 1],
            [0, 0, 0],
            [0, 0, 0]
        ],
        '`': [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ],
        "'": [
            [0, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ],
        '"': [
            [1, 0, 1],
            [1, 0, 1],
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ],
        '•': [
            [0, 0, 0],
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
            [0, 0, 0]
        ],
        '>': [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0]
        ]
    }
    
    # Add lowercase letters (same as uppercase for simplicity)
    for char in list('abcdefghijklmnopqrstuvwxyz'):
        font[char] = font[char.upper()]
        
    return font

def main():
    """Main function to run the rainbow text pipe."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize the display
    display = UnicornHATMini()
    
    # Set brightness
    brightness = max(0.1, min(1.0, args.brightness))
    display.set_brightness(brightness)
    
    # Create and run the text pipe
    pipe = RainbowTextPipe(
        display=display,
        initial_text=args.initial_text,
        font_path=args.font,
        initial_speed=args.speed,
        max_length=args.max_length,
        separator=args.separator,
        use_stdin=not args.no_stdin
    )
    
    # Check if there's input on stdin already
    if not sys.stdin.isatty() and not args.no_stdin:
        # Read initial input from stdin
        try:
            for line in sys.stdin:
                line = line.strip()
                if line:
                    pipe.add_text(line)
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    
    pipe.run()


if __name__ == "__main__":
    main()
