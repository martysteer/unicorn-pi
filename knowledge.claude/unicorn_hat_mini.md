# Unicorn HAT Mini Knowledge File
**Source:** https://learn.pimoroni.com/article/getting-started-with-unicorn-hat-mini

## General Information

- **Product Name:** Unicorn HAT Mini
- **Type:** RGB LED matrix (17x7 pixels) HAT for Raspberry Pi
- **Hardware Notes:** Uses Holtek matrix driver chips (not Neopixels/WS2812)
- **Physical Interface:** Pre-soldered header, no soldering required
- **Communication Protocol:** SPI

## Setup Requirements

### Software Installation
```bash
# Enable SPI
sudo raspi-config nonint do_spi 0

# Install library
git clone https://github.com/pimoroni/unicornhatmini-python
cd unicornhatmini-python
sudo ./install.sh

# Optional: Remove installer files
sudo rm -r ~/unicornhatmini-python

# Examples location
cd ~/Pimoroni/unicornhatmini/examples
```

### OS Recommendation
- Full desktop version of Raspberry Pi OS (latest)
- SPI must be enabled

## Library Usage

### Basic Setup
```python
from unicornhatmini import UnicornHATMini
uh = UnicornHATMini()

# Set brightness (recommended 0.5 or lower)
uh.set_brightness(0.5)
```

### Pixel Control
- **Coordinate System:** Top-left is (0,0), bottom-right is (16,6)
- **Color Format:** RGB values (0-255 for each channel)
- **Brightness Warning:** 100% brightness can be very intense

### Essential Functions
```python
# Set a single pixel
uh.set_pixel(x, y, r, g, b)  # Example: uh.set_pixel(0, 0, 255, 0, 0) for red

# Display pixels after setting them
uh.show()

# Clear all pixels
uh.clear()
uh.show()
```

## Code Examples

### Light All Pixels
```python
for x in range(17):
    for y in range(7):
        uh.set_pixel(x, y, 0, 255, 255)  # Cyan
uh.show()
```

### Blinking Effect
```python
import time

while True:
    for x in range(17):
        for y in range(7):
            uh.set_pixel(x, y, 255, 0, 255)  # Pink
    uh.show()
    time.sleep(0.25)
    uh.clear()
    uh.show()
    time.sleep(0.25)
```

### Rainbow Animation
```python
import time
import colorsys

spacing = 360.0 / 34.0
hue = 0

while True:
    hue = int(time.time() * 100) % 360
    for x in range(17):
        offset = x * spacing
        h = ((hue + offset) % 360) / 360.0
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
        for y in range(7):
            uh.set_pixel(x, y, r, g, b)
    uh.show()
    time.sleep(0.05)
```

## Technical Notes

- HSV color model can be used through the colorsys library for easier rainbow effects
- Recommended to keep animation delays (time.sleep) to maintain performance
- Maximum brightness (1.0) is very intense - 0.5 is recommended for most use cases

## Project Ideas

- Cheerlights integration (display current Cheerlights color)
- Twitter mood light (based on sentiment analysis)
- Office busy indicator (via Google Calendar/Zoom/Teams integration)
- Weather display
- System status monitor

## Troubleshooting

- If pixels don't light up, ensure SPI is enabled
- Always call uh.show() after setting pixels to display changes
- For display issues, check the brightness setting