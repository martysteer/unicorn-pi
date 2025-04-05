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
        from proxyunicornhatmini import UnicornHATMini
        print("Using proxy UnicornHATMini implementation for macOS")
    except ImportError:
        raise ImportError("Error: proxyunicornhatmini.py not found in the current directory or PYTHONPATH.")
else:  # Raspberry Pi or other Linux system
    try:
        from unicornhatmini import UnicornHATMini
        print("Using actual UnicornHATMini implementation")
    except ImportError:
        raise ImportError("Error: Unicorn HAT Mini library not found. Please install it with: sudo pip3 install unicornhatmini")

# Add platform-specific processing method to UnicornHATMini
if platform.system() == "Darwin":
    # For macOS proxy version
    UnicornHATMini.process_events = lambda self: self.show()
else:
    # For actual hardware, no action needed
    UnicornHATMini.process_events = lambda self: None

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
