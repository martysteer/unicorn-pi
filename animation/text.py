#!/usr/bin/env python3
"""
Text animations for Unicorn HAT Mini.

This module contains text-based animations that can display static and
animated text on the Unicorn HAT Mini display.
"""

import time
import colorsys
from PIL import Image, ImageDraw, ImageFont

from animation import Animation, register_animation

class CustomPixelFont:
    """A custom pixel font for rendering text on small displays."""
    
    def __init__(self):
        """Initialize the custom pixel font."""
        self.char_width = 3  # Width of each character in pixels
        self.char_height = 5  # Height of each character in pixels
        self.char_spacing = 1  # Spacing between characters
        self.bitmap_font = self._create_pixel_bitmap_font()
    
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
    
    def _create_pixel_bitmap_font(self):
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
            # ... Add more characters as needed
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
            '-': [
                [0, 0, 0],
                [0, 0, 0],
                [1, 1, 1],
                [0, 0, 0],
                [0, 0, 0]
            ]
        }
        
        # Add lowercase letters (same as uppercase for simplicity)
        for char in list('abcdefghijklmnopqrstuvwxyz'):
            font[char] = font[char.upper()]
            
        return font


@register_animation(name="TextAnimation")
class TextAnimation(Animation):
    """Base class for text animations.
    
    This class provides the foundation for all text-based animations,
    handling text rendering, positioning, and basic configuration.
    """
    
    def setup(self):
        """Set up the text animation."""
        super().setup()
        
        # Get text from config
        self.text = self.config.get('text', 'Hello World')
        
        # Font configuration
        self.use_custom_font = self.config.get('use_custom_font', True)
        self.font_path = self.config.get('font_path', None)
        self.font_size = self.config.get('font_size', 8)
        
        # Position configuration
        self.position = self.config.get('position', 'center')  # 'center', 'top', 'bottom', or (x, y)
        
        # Color configuration
        self.color_mode = self.config.get('color_mode', 'static')  # 'static', 'rainbow', 'pulse'
        self.color = self.config.get('color', (255, 255, 255))  # Default white
        
        # Set up the font
        self.setup_font()
        
        # Measure text dimensions
        self.measure_text()
        
        # Create text image
        self.create_text_image()
    
    def setup_font(self):
        """Set up the font for text rendering."""
        if self.use_custom_font:
            # Use our custom pixel font
            self.font = CustomPixelFont()
            print(f"Using custom pixel font for '{self.text}'")
        else:
            # Try to load a system font
            try:
                if self.font_path:
                    self.font = ImageFont.truetype(self.font_path, self.font_size)
                else:
                    # Try common system fonts, fall back to default
                    try:
                        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.font_size)
                    except IOError:
                        self.font = ImageFont.load_default()
            except Exception as e:
                print(f"Font error: {e}")
                self.font = ImageFont.load_default()
                
            print(f"Using PIL font for '{self.text}'")
    
    def measure_text(self):
        """Measure the text dimensions for positioning."""
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
            
        print(f"Text dimensions: {self.text_width}x{self.text_height}")
    
    def create_text_image(self):
        """Create the text image with current settings."""
        # Create an image large enough to hold the text
        self.text_image = Image.new("RGB", (max(1, self.text_width), self.height), (0, 0, 0))
        draw = ImageDraw.Draw(self.text_image)
        
        # Calculate position for text
        if self.position == 'center':
            x = 0  # For text image, always start at left edge
            y = (self.height - self.text_height) // 2
        elif self.position == 'top':
            x = 0
            y = 0
        elif self.position == 'bottom':
            x = 0
            y = self.height - self.text_height
        elif isinstance(self.position, tuple) and len(self.position) == 2:
            # Custom position
            x = 0
            y = self.position[1]
        else:
            # Default to center
            x = 0
            y = (self.height - self.text_height) // 2
        
        # Render the text
        if isinstance(self.font, CustomPixelFont):
            # Use our custom pixel font renderer
            self.font.render_text(draw, self.text, (x, y), self.color)
        else:
            # Use PIL's text rendering
            draw.text((x, y), self.text, font=self.font, fill=self.color)
            
        print(f"Created text image at position ({x}, {y})")
    
    def get_color(self, x, y, t):
        """Get color for a pixel based on the color mode.
        
        Args:
            x: X-coordinate of the pixel
            y: Y-coordinate of the pixel
            t: Current time in seconds
            
        Returns:
            RGB color tuple (r, g, b)
        """
        if self.color_mode == 'static':
            # Static color
            return self.color
        
        elif self.color_mode == 'rainbow':
            # Rainbow color based on position
            char_position = x / float(max(1, self.text_width))
            hue = (char_position + t * 0.2) % 1.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            return (r, g, b)
        
        elif self.color_mode == 'pulse':
            # Pulsing color effect
            pulse = (math.sin(t * 2) + 1) / 2  # 0.0 to 1.0
            if isinstance(self.color, tuple) and len(self.color) == 3:
                r, g, b = self.color
                r = int(r * pulse)
                g = int(g * pulse)
                b = int(b * pulse)
                return (r, g, b)
            else:
                # Default to pulsing white
                v = int(255 * pulse)
                return (v, v, v)
        
        # Default to static color
        return self.color
    
    def update(self, dt):
        """Update the text animation."""
        self.display.clear()
        
        # Calculate center position for the text image
        x_pos = (self.width - self.text_width) // 2
        y_pos = 0  # Not needed since vertical positioning is handled in the text image
        
        # Draw the text image with current color mode
        for y in range(self.height):
            for x in range(self.width):
                text_x = x - x_pos
                
                # Only process pixels within the text image
                if 0 <= text_x < self.text_width:
                    # Get the pixel from the text image
                    pixel = self.text_image.getpixel((text_x, y))
                    
                    # If the pixel is not black (i.e., part of the text)
                    if pixel != (0, 0, 0):
                        # Get color based on our color mode
                        color = self.get_color(text_x, y, time.time() - self.start_time)
                        self.display.set_pixel(x, y, *color)


@register_animation(name="StaticTextAnimation")
class StaticTextAnimation(TextAnimation):
    """Static text animation that displays fixed text in the center of the screen.
    
    This is the simplest text animation, showing static text with optional color effects.
    """
    
    def setup(self):
        """Set up the static text animation."""
        # Call the parent setup to initialize everything
        super().setup()
        
        # Set up any specific configuration for static text
        self.display_offset = self.config.get('offset', (0, 0))
        
        print(f"Static text animation set up with text: '{self.text}'")
    
    def update(self, dt):
        """Update the static text animation."""
        self.display.clear()
        
        # Calculate position with offset
        offset_x, offset_y = self.display_offset
        x_pos = ((self.width - self.text_width) // 2) + offset_x
        
        # Draw the text image with current color mode
        for y in range(self.height):
            for x in range(self.width):
                text_x = x - x_pos
                
                # Only process pixels within the text image
                if 0 <= text_x < self.text_width:
                    # Get the pixel from the text image
                    pixel = self.text_image.getpixel((text_x, y))
                    
                    # If the pixel is not black (i.e., part of the text)
                    if pixel != (0, 0, 0):
                        # Get color based on our color mode
                        color = self.get_color(text_x, y, time.time() - self.start_time)
                        self.display.set_pixel(x, y, *color)
