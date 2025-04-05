#!/usr/bin/env python3
"""
Utility module for Unicorn HAT Mini applications.
Contains common functions used across multiple Unicorn HAT Mini applications
and proxy implementation for cross-platform support.
"""

import os
import platform
import sys
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps

# First, determine which UnicornHATMini implementation to use based on platform
if platform.system() == "Darwin":  # macOS
    try:
        # Import the proxy implementation
        from proxyunicornhatmini import UnicornHATMiniBase
        print("Using proxy UnicornHATMini implementation for macOS")
    except ImportError:
        raise ImportError("Error: proxyunicornhatmini.py not found in the current directory or PYTHONPATH.")
else:  # Raspberry Pi or other Linux system
    try:
        from unicornhatmini import UnicornHATMini as UnicornHATMiniBase
        print("Using actual UnicornHATMini implementation")
    except ImportError:
        raise ImportError("Error: Unicorn HAT Mini library not found. Please install it with: sudo pip3 install unicornhatmini")


class UnicornHATMini:
    """
    A wrapper class for UnicornHATMini that provides a consistent interface
    across both the actual hardware and the proxy implementation.
    """
    
    # Constants from UnicornHATMini
    BUTTON_A = 5
    BUTTON_B = 6
    BUTTON_X = 16
    BUTTON_Y = 24
    
    def __init__(self, *args, **kwargs):
        # Initialize the appropriate implementation
        self.unicorn = UnicornHATMiniBase(*args, **kwargs)
        self._platform = "proxy" if platform.system() == "Darwin" else "actual"
        
        # Initialize button state
        self.button_callback = None
        
        # For actual hardware, import and setup GPIOZero buttons
        if self._platform == "actual":
            try:
                from gpiozero import Button
                
                # Initialize the buttons
                self.buttons = {
                    self.BUTTON_A: Button(self.BUTTON_A),
                    self.BUTTON_B: Button(self.BUTTON_B),
                    self.BUTTON_X: Button(self.BUTTON_X),
                    self.BUTTON_Y: Button(self.BUTTON_Y)
                }
            except ImportError:
                print("Warning: GPIOZero not found. Button functionality will be limited.")
                self.buttons = {}
    
    def on_button_pressed(self, callback):
        """
        Register a callback for button press events.
        Works across both proxy and actual implementations.
        
        Args:
            callback: Function to call when a button is pressed. 
                     It will receive the button pin number as an argument.
        """
        self.button_callback = callback
        
        if self._platform == "proxy":
            # For the proxy, use its built-in method
            if hasattr(self.unicorn, 'on_button_pressed'):
                self.unicorn.on_button_pressed(callback)
        else:
            # For actual hardware, use GPIOZero's when_pressed
            if hasattr(self, 'buttons') and self.buttons:
                for pin, button in self.buttons.items():
                    # Use a lambda with a default argument to capture current pin value
                    button.when_pressed = lambda btn=pin: self.button_callback(btn)
    
    def read_button(self, pin):
        """
        Read the current state of a button.
        Works across both proxy and actual implementations.
        
        Args:
            pin: Button pin number (5, 6, 16, or 24)
        
        Returns:
            True if button is pressed, False otherwise
        """
        if self._platform == "proxy":
            # For the proxy, use its built-in method
            if hasattr(self.unicorn, 'read_button'):
                return self.unicorn.read_button(pin)
        else:
            # For actual hardware, check if the button is pressed
            if hasattr(self, 'buttons') and pin in self.buttons:
                return self.buttons[pin].is_pressed
        return False
    
    def process_events(self):
        """
        Process events (needed for proxy implementation).
        For actual hardware, this is a no-op.
        """
        if self._platform == "proxy" and hasattr(self.unicorn, 'process_events'):
            self.unicorn.process_events()
    
    # Delegate all other methods to the wrapped UnicornHATMini instance
    def __getattr__(self, name):
        return getattr(self.unicorn, name)

# Utility functions

def process_image(image, rotation=0, flip_horizontal=False):
    """
    Process image based on current transformation settings.
    
    Args:
        image: The original PIL Image
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        flip_horizontal: Whether to flip the image horizontally
        
    Returns:
        Processed PIL Image ready for display
    """
    # Make a copy of the image to avoid modifying the original
    img = image.copy()
    
    # Apply horizontal flip if needed
    if flip_horizontal:
        img = ImageOps.mirror(img)
    
    # Apply rotation if needed
    if rotation != 0:
        img = img.rotate(rotation, expand=True)
    
    # Resize based on the Unicorn HAT Mini dimensions
    display_width = 17  # Unicorn HAT Mini width
    display_height = 7  # Unicorn HAT Mini height
    
    # Calculate scaling ratios
    width_ratio = display_width / img.width
    height_ratio = display_height / img.height
    ratio = min(width_ratio, height_ratio)
    
    # Resize the image maintaining aspect ratio
    new_width = int(img.width * ratio)
    new_height = int(img.height * ratio)
    resized_image = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Create a canvas of the display size
    result = Image.new("RGB", (display_width, display_height), (0, 0, 0))
    
    # Calculate position to center the image
    x_offset = (display_width - new_width) // 2
    y_offset = (display_height - new_height) // 2
    
    # Paste the resized image centered
    result.paste(resized_image, (x_offset, y_offset))
    
    return result

def display_info_message(display, message, submessage=""):
    """
    Display a message in the center of the screen.
    
    Args:
        display: UnicornHATMini instance
        message: Main message to display
        submessage: Optional secondary message to display below the main message
    """
    # Get display dimensions from the display
    width, height = display.get_shape()
    
    # Create a blank image with black background
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if necessary
    try:
        main_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 8)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 6)
    except IOError:
        main_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
    
    # Get text size for centering
    try:
        # For newer PIL versions
        _, _, text_width, text_height = draw.textbbox((0, 0), message, font=main_font)
    except AttributeError:
        # Fallback for older PIL versions
        text_width, text_height = draw.textsize(message, font=main_font)
    
    # Calculate position to center the text
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2 - 1 if submessage else (height - text_height) // 2
    
    # Draw the main message
    draw.text((text_x, text_y), message, font=main_font, fill=(255, 255, 255))
    
    # Draw submessage if provided
    if submessage:
        try:
            # For newer PIL versions
            _, _, subtext_width, subtext_height = draw.textbbox((0, 0), submessage, font=sub_font)
        except AttributeError:
            # Fallback for older PIL versions
            subtext_width, subtext_height = draw.textsize(submessage, font=sub_font)
        
        subtext_x = (width - subtext_width) // 2
        subtext_y = text_y + text_height + 1
        
        draw.text((subtext_x, subtext_y), submessage, font=sub_font, fill=(200, 200, 200))
    
    # Set each pixel on the Unicorn HAT Mini
    for y in range(height):
        for x in range(width):
            r, g, b = image.getpixel((x, y))
            display.set_pixel(x, y, r, g, b)
    
    # Update the display
    display.show()

def load_image(image_path):
    """
    Load an image file with error handling.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        PIL Image object or None if loading failed
    """
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Convert image to RGB mode if it's not already
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        return image
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def clear_display(display):
    """
    Clear the display with a black screen.
    
    Args:
        display: UnicornHATMini instance
    """
    display.clear()
    display.show()
    display.set_brightness(0)  # Turn off backlight completely