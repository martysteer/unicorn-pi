#!/usr/bin/env python3
import time
import sys
from colorsys import hsv_to_rgb
from PIL import Image, ImageDraw, ImageFont
from unicornhatmini import UnicornHATMini

# Initialize the Unicorn HAT Mini
unicornhatmini = UnicornHATMini()

# Set rotation to 0 by default, can be changed via command line argument
rotation = 0
if len(sys.argv) > 1:
    try:
        rotation = int(sys.argv[1])
    except ValueError:
        print("Usage: {} <rotation>".format(sys.argv[0]))
        sys.exit(1)

unicornhatmini.set_rotation(rotation)

# Hardcode the display dimensions for Unicorn HAT Mini
display_width = 17
display_height = 7

print("Display dimensions: {}x{}".format(display_width, display_height))

# Set a moderate brightness to avoid eye strain
unicornhatmini.set_brightness(0.3)

# The text we want to display
text = "DEMO"

# Load a 5x7 pixel font
try:
    font = ImageFont.truetype("5x7.ttf", 8)
except IOError:
    # Fallback to a default font if 5x7.ttf is not available
    font = ImageFont.load_default()
    print("Warning: 5x7.ttf font not found, using default font")

# Measure the size of our text
# Using newer Pillow API to get text dimensions
try:
    # For newer Pillow versions
    left, top, right, bottom = font.getbbox(text)
    text_width = right - left
    text_height = bottom - top
except AttributeError:
    try:
        # Fallback for older Pillow versions that don't have getbbox
        text_width, text_height = font.getsize(text)
    except AttributeError:
        # Another fallback approach if neither method is available
        dummy_draw = ImageDraw.Draw(Image.new('P', (1, 1)))
        text_width, text_height = dummy_draw.textsize(text, font=font)

print(f"Text dimensions: {text_width}x{text_height}")

# Calculate how much we need to scroll to show all text
scroll_width = text_width + (2 * display_width)  # Provide more space for scrolling

# Create a new PIL image big enough to fit the text and display width
image = Image.new('P', (scroll_width, display_height), 0)
draw = ImageDraw.Draw(image)

# Calculate vertical position to center the text
y_position = (display_height - text_height) // 2
if y_position < 0:
    y_position = 0  # Ensure text isn't positioned off-screen

# Draw the text into the image (white color = 255)
# Position text so it starts off-screen and scrolls in from the right
draw.text((display_width, y_position), text, font=font, fill=255)

# Set initial offset for scrolling
offset_x = 0

# Enable for rainbow text mode (set to True for colorful text)
rainbow_mode = False

try:
    while True:
        # Clear the display
        unicornhatmini.clear()
        
        # Draw the current portion of the text image to the display
        for y in range(display_height):
            for x in range(display_width):
                # If the pixel in our image is lit (255), set it with color on the display
                if x + offset_x < image.size[0] and image.getpixel((x + offset_x, y)) == 255:
                    if rainbow_mode:
                        # Create a rainbow effect based on position
                        hue = (time.time() / 10.0) + (x / float(display_width * 2))
                        r, g, b = [int(c * 255) for c in hsv_to_rgb(hue, 1.0, 1.0)]
                        unicornhatmini.set_pixel(x, y, r, g, b)
                    else:
                        # Just use white for simplicity
                        unicornhatmini.set_pixel(x, y, 255, 255, 255)
                else:
                    unicornhatmini.set_pixel(x, y, 0, 0, 0)  # Black (off)
        
        # Update the display
        unicornhatmini.show()
        
        # Increment the offset to create scrolling effect
        offset_x += 1
        if offset_x >= scroll_width:
            offset_x = 0
        
        # Control the scrolling speed
        time.sleep(0.1)

except KeyboardInterrupt:
    # Turn off all LEDs when the program is interrupted
    unicornhatmini.clear()
    unicornhatmini.show()
    print("Exiting")
