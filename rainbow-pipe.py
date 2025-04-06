#!/usr/bin/env python3
"""
Rainbow Text Pipe for Unicorn HAT Mini

A script that scrolls multicolored text from stdin with interactive button controls:
- Button A: Toggle between slow, medium, and fast scroll speeds
- Button B: Cycle through different color animation effects
- Button X: Move text baseline down
- Button Y: Move text baseline up
- Button A+B (long press): Toggle static display mode in livefeed mode

Usage: 
  - With default text: python rainbow-pipe.py
  - With piped input: echo "Hello world" | python rainbow-pipe.py --no-default
  - With live feed mode: tail -f log.txt | python rainbow-pipe.py --livefeed

Options:
  --no-default: Don't show default text when piping input
  --livefeed: Enable live feed mode (resets display when input pauses)
  --no-static: Disable static display mode on Enter key in livefeed mode

In live feed mode:
- The display will reset if there's a pause in the input stream
- When the user presses Enter, the current text stops scrolling and displays statically
- Press A+B buttons together to toggle between scrolling and static display
"""

import argparse
import time
import math
import colorsys
import random
import sys
import threading
import select
import queue
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
    
    parser.add_argument('--text', type=str, default="",
                       help='Text to scroll across the display (default: read from stdin)')
    
    parser.add_argument('--brightness', '-b', type=float, default=0.5,
                       help='Display brightness (0.0-1.0)')
    
    parser.add_argument('--font', type=str, default=None,
                       help='Path to TTF font file (default: built-in font)')
    
    parser.add_argument('--speed', type=str, default='medium',
                       choices=['slow', 'medium', 'fast'],
                       help='Initial scroll speed')
    
    parser.add_argument('--livefeed', action='store_true',
                       help='Enable live feed mode (resets display when input pauses)')
    
    parser.add_argument('--timeout', type=float, default=2.0,
                       help='Timeout in seconds for live feed mode reset (default: 2.0)')
    
    parser.add_argument('--gap', type=int, default=16,
                       help='Gap between text repetitions in pixels (default: 16)')
    
    parser.add_argument('--no-default', action='store_true',
                       help='Do not show default text when piping input')
    
    parser.add_argument('--no-static', action='store_true',
                       help='Disable static display mode on Enter in livefeed mode')
    
    return parser.parse_args()


class InputReader(threading.Thread):
    """Thread for reading input from stdin without blocking the main thread."""
    
    def __init__(self, input_queue, livefeed_mode=False, timeout=2.0, static_on_enter=True):
        """Initialize the input reader thread."""
        super().__init__(daemon=True)
        self.input_queue = input_queue
        self.livefeed_mode = livefeed_mode
        self.timeout = timeout
        self.running = True
        self.last_input_time = time.time()
        self.buffer = ""
        self.static_on_enter = static_on_enter and livefeed_mode
    
    def run(self):
        """Run the input reader thread."""
        if self.livefeed_mode:
            # Live feed mode - read characters in chunks
            while self.running:
                # Check if there's input available
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    # Read a chunk of input (more efficient than one character at a time)
                    chunk = sys.stdin.read(64)  # Read up to 64 chars at once
                    if chunk:  # If not EOF
                        self.buffer += chunk
                        # Process the buffer to handle newlines
                        if '\n' in self.buffer:
                            lines = self.buffer.split('\n')
                            # Keep the last incomplete line in the buffer
                            self.buffer = lines.pop()
                            # Send complete lines to the queue
                            for line in lines:
                                if line:  # Skip empty lines
                                    # Add a special marker for Enter key if enabled
                                    if self.static_on_enter:
                                        self.input_queue.put(line + '\0STATIC\0')
                                    else:
                                        self.input_queue.put(line + '\n')
                        self.last_input_time = time.time()
                else:
                    # Send any remaining buffered content after a short pause
                    if self.buffer and time.time() - self.last_input_time > self.timeout/2:
                        self.input_queue.put(self.buffer)
                        self.buffer = ""
                    
                    # Check if we need to reset due to timeout
                    if time.time() - self.last_input_time > self.timeout:
                        # Send a reset signal (special marker that won't appear in normal text)
                        self.input_queue.put("\0RESET\0")  
                        self.last_input_time = time.time()
        else:
            # Normal mode - read lines
            for line in sys.stdin:
                if not self.running:
                    break
                self.input_queue.put(line)
                
                # In case stdin is done but we're not detecting it properly
                if not select.select([sys.stdin], [], [], 0.0)[0]:
                    break


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


class RainbowPipeScroller:
    """Controls the scrolling text display and button interactions."""
    
    def __init__(self, display, initial_text="", font_path=None, initial_speed='medium', 
                 livefeed_mode=False, timeout=2.0, gap_width=16, static_on_enter=True):
        """Initialize the rainbow text scroller."""
        self.display = display
        self.width, self.height = display.get_shape()
        self.font_path = font_path
        self.scroll_x = self.width  # Start scrolling from right edge
        self.livefeed_mode = livefeed_mode
        self.input_timeout = timeout
        self.use_custom_pixel_font = True  # Use the custom pixel font by default
        self.static_on_enter = static_on_enter and livefeed_mode
        self.static_display = False  # Flag to indicate static display mode
        
        # Input handling
        self.input_queue = queue.Queue()
        self.input_reader = InputReader(self.input_queue, livefeed_mode, timeout, static_on_enter)
        self.input_reader.start()
        self.text_buffer = initial_text
        self.last_buffer_update = time.time()
        self.needs_redraw = True
        
        # Scrolling parameters
        self.speed_settings = {
            'slow': 0.1,    # pixels per frame
            'medium': 0.2,  # pixels per frame
            'fast': 0.4     # pixels per frame
        }
        self.current_speed = initial_speed
        self.scroll_step = self.speed_settings[self.current_speed]
        
        # Add a gap between repeated scrolls for a smooth marquee effect
        self.gap_width = gap_width
        
        # Text baseline position (vertical centering)
        self.baseline_y = self.height // 2  # Default to vertically centered
        
        # Color effects
        self.color_modes = ['static_rainbow', 'wave', 'pulse', 'random_flash']
        self.current_color_mode = 0  # Start with static rainbow
        self.color_time = 0          # For time-based effects
        self.flash_countdown = 0     # For random flash effect
        
        # Text image
        self.font = None
        self.text_image = None
        self.text_width = 0
        self.text_height = 0
        
        # Set up text rendering
        self.setup_font()
        if self.text_buffer:
            self.update_text_image()
        
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
                    # Try to load a system font, fall back to default if not available
                    try:
                        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
                    except IOError:
                        self.font = ImageFont.load_default()
            except Exception as e:
                print(f"Font error: {e}")
                self.font = ImageFont.load_default()
    
    def update_text_image(self):
        """Update the text image based on the current text buffer."""
        if not self.text_buffer:
            self.text_image = Image.new("RGB", (1, self.height), (0, 0, 0))
            self.text_width = 1
            self.text_height = 0
            return
            
        # Measure the size of our text
        try:
            if isinstance(self.font, CustomPixelFont):
                # Use our custom pixel font methods
                left, top, right, bottom = self.font.getbbox(self.text_buffer)
                self.text_width = right - left
                self.text_height = bottom - top
            else:
                # For PIL fonts
                try:
                    # For newer PIL versions
                    left, top, right, bottom = self.font.getbbox(self.text_buffer)
                    self.text_width = right - left
                    self.text_height = bottom - top
                except AttributeError:
                    # Fallback for older PIL versions
                    self.text_width, self.text_height = self.font.getsize(self.text_buffer)
        except Exception as e:
            print(f"Error measuring text: {e}")
            # Fallback values
            self.text_width = len(self.text_buffer) * 5
            self.text_height = 5
        
        # Create a buffer that's the size needed for the text
        self.text_image = Image.new("RGB", (max(1, self.text_width), self.height), (0, 0, 0))
        draw = ImageDraw.Draw(self.text_image)
        
        # Draw the text in the buffer
        y_position = self.baseline_y - self.text_height // 2
        
        if isinstance(self.font, CustomPixelFont):
            # Use our custom pixel font renderer
            self.font.render_text(draw, self.text_buffer, (0, y_position), (255, 255, 255))
        else:
            # Use PIL's text rendering with pixel-perfect mode
            draw.text((0, y_position), self.text_buffer, font=self.font, fill=(255, 255, 255))
        
        # Always reset scroll position to start from the right edge
        self.scroll_x = self.width
    
    def check_input(self):
        """Check for new input from stdin."""
        # Process all available input
        reset_signal = False
        new_input = False
        static_signal = False
        
        while not self.input_queue.empty():
            new_input = True
            text = self.input_queue.get()
            
            # Check for reset signal in livefeed mode
            if self.livefeed_mode and text == "\0RESET\0":
                reset_signal = True
                self.text_buffer = ""
                self.static_display = False
                print("[LiveFeed] Reset detected - clearing display")
                break
                
            # Check for static display signal in livefeed mode
            if self.livefeed_mode and self.static_on_enter and text.endswith("\0STATIC\0"):
                static_signal = True
                # Remove the marker and add the text
                clean_text = text.replace("\0STATIC\0", "")
                print(f"[LiveFeed] Static display mode: '{clean_text}'")
                # Store previous text width for transition calculations
                prev_width = self.text_width if self.text_image else 0
                self.text_buffer = clean_text
                # Update the text image to get new dimensions
                self.update_text_image()
                # Enable static display and center the text
                self.static_display = True
                self.scroll_x = (self.width - self.text_width) // 2
                break
            
            # In livefeed mode, handle reset and scrolling differently
            if self.livefeed_mode and not static_signal:
                # If text has scrolled mostly off screen, clear it
                if self.scroll_x < -self.text_width * 0.7 and not self.static_display:
                    self.text_buffer = ""
                    self.scroll_x = self.width
                
                # Replace newlines with spaces for continuous display
                text = text.replace("\n", " ")
            
            # Append the new text to our buffer
            self.text_buffer += text
        
        # If we got new input or a reset signal, update the text image
        if new_input or reset_signal:
            self.update_text_image()
            self.needs_redraw = True
            self.last_buffer_update = time.time()
    
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
            self.update_text_image()  # Redraw text with new baseline
            self.needs_redraw = True
    
    def handle_buttons(self):
        """Check for button presses and handle accordingly."""
        buttons = {
            self.display.BUTTON_A: self.change_speed,
            self.display.BUTTON_B: self.change_color_mode,
            self.display.BUTTON_X: lambda: self.move_baseline(1),   # Down (increase Y)
            self.display.BUTTON_Y: lambda: self.move_baseline(-1),  # Up (decrease Y),
        }
        
        # Add a special button handler for static mode toggle
        if self.livefeed_mode and self.static_on_enter:
            # Long press A+B together to toggle static mode
            if self.display.read_button(self.display.BUTTON_A) and self.display.read_button(self.display.BUTTON_B):
                # Check if both buttons were pressed for at least 0.5 seconds
                # We'll use the stored times in prev_button_states for this check
                ab_press_time = self.prev_button_states.get('ab_press_time', 0)
                if ab_press_time > 0 and time.time() - ab_press_time > 0.5:
                    self.static_display = not self.static_display
                    print(f"[LiveFeed] Static display mode: {'enabled' if self.static_display else 'disabled'}")
                    self.needs_redraw = True
                    
                    # For static mode, center the text
                    if self.static_display:
                        self.scroll_x = (self.width - self.text_width) // 2
                    else:
                        self.scroll_x = self.width  # Reset scroll position
                        
                    # Reset button press time to avoid toggling multiple times
                    self.prev_button_states['ab_press_time'] = time.time()
                    return  # Skip normal button processing
            else:
                # Start tracking A+B press time
                if self.display.read_button(self.display.BUTTON_A) or self.display.read_button(self.display.BUTTON_B):
                    if 'ab_press_time' not in self.prev_button_states:
                        self.prev_button_states['ab_press_time'] = time.time()
        
        for button, action in buttons.items():
            # Get previous and current button state
            prev_state = self.prev_button_states.get(button, False)
            curr_state = self.display.read_button(button)
            
            # Update previous state for next time
            self.prev_button_states[button] = curr_state
            
            # Check for a button press (transition from not pressed to pressed)
            if curr_state and not prev_state:
                action()
                self.needs_redraw = True
    
    def get_pixel_color(self, x, text_x, y):
        """Determine the color for a specific pixel based on the current color mode."""
        # Get a normalized position of this character in the text (0.0 to 1.0)
        char_position = text_x / max(1, self.text_width)
        
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
    
    def update(self):
        """Update the display with the current frame of scrolling text."""
        # Check for new input
        self.check_input()
        
        # Skip rendering if we have no text
        if not self.text_buffer or self.text_width <= 0:
            # Clear the display if needed
            if self.needs_redraw:
                self.display.clear()
                self.display.show()
                self.needs_redraw = False
            return
        
        # Update the scroll position if not in static display mode
        if not self.static_display:
            self.scroll_x -= self.scroll_step
            self.needs_redraw = True
        else:
            # In static display mode, center the text
            self.scroll_x = (self.width - self.text_width) // 2
        
        # If the text has completely scrolled off the left edge (plus gap), reset
        if not self.static_display and self.scroll_x < -self.text_width - self.gap_width:
            self.scroll_x = self.width  # Reset to start off-screen to the right
        
        # Clear the display
        self.display.clear()
        
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
    
    def run(self):
        """Run the main loop of the text scroller."""
        try:
            # Show welcome message if not in livefeed mode
            if not self.livefeed_mode:
                display_info_message(self.display, "Rainbow", "Pipe")
                time.sleep(0.5)
            
            # Check if stdin is a terminal or a pipe
            is_pipe = not sys.stdin.isatty()
            
            # If stdin is a terminal and we have no initial text, show a prompt
            if not is_pipe and not self.text_buffer:
                print("Type text and press Enter (Ctrl+D to end):")
            
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
            self.input_reader.running = False
            clear_display(self.display)
            print("Display cleared")


def main():
    """Main function to run the rainbow pipe scroller."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Initialize the display
    display = UnicornHATMini()
    
    # Set brightness
    brightness = max(0.1, min(1.0, args.brightness))
    display.set_brightness(brightness)
    
    # Check if we have piped input
    has_piped_input = not sys.stdin.isatty()
    
    # Determine initial text
    if has_piped_input and (args.no_default or args.livefeed):
        # If piping input with --no-default or --livefeed, start with empty text
        initial_text = ""
    else:
        # Otherwise use the provided text or default
        initial_text = args.text or "Unicorn HAT Mini > "
    
    # If not using livefeed and no explicit text is provided, try to read initial stdin
    if not args.livefeed and not args.text and has_piped_input:
        if select.select([sys.stdin], [], [], 0.0)[0]:
            # Non-blocking read from stdin
            initial_text = sys.stdin.read()
    
    # Create and run the text scroller
    # Only enable static display on Enter if livefeed mode is active
    static_on_enter = args.livefeed and not args.no_static
    
    scroller = RainbowPipeScroller(
        display=display,
        initial_text=initial_text,
        font_path=args.font,
        initial_speed=args.speed,
        livefeed_mode=args.livefeed,
        timeout=args.timeout,
        gap_width=args.gap,
        static_on_enter=static_on_enter
    )
    
    scroller.run()


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
        ]
    }
    
    # Add lowercase letters (same as uppercase for simplicity)
    for char in list('abcdefghijklmnopqrstuvwxyz'):
        font[char] = font[char.upper()]
        
    return font


if __name__ == "__main__":
    main()