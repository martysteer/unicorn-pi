# Unicorn HAT Mini Project Overview

This repository contains a collection of Python scripts and tools for the Pimoroni Unicorn HAT Mini, which is an RGB LED matrix HAT (Hardware Attached on Top) for the Raspberry Pi. The HAT features a 17x7 LED matrix and four buttons.

## Core Library Structure

The repository is organized with:

1. **Main Library** (`unicornhatmini`, found in `library/unicornhatmini/__init__.py`)
2. **Utility Wrappers** (`unicornhatutils.py`, `proxydisplayhatmini.py`)
3. **Example Applications**
4. **Animation Framework** (in the `animation/` directory)
5. **Pi Day 2025 Poster Tools** (in the `piday2025posters/` directory)

## Core Functionality

### LED Matrix Control

The library provides functions to:

- Set individual pixels with RGB colors (`set_pixel(x, y, r, g, b)`)
- Set all pixels to a single color (`set_all(r, g, b)`)
- Clear the display (`clear()`)
- Control brightness (`set_brightness(value)`)
- Set rotation (0, 90, 180, 270 degrees) (`set_rotation(degrees)`)
- Render entire images to the display (`set_image()`)
- Update the display to show changes (`show()`)

### Button Handling

The HAT includes four buttons labeled A, B, X, and Y on pins 5, 6, 16, and 24:

- Reading button state (`read_button(button_pin)`)
- Registering callback functions (`on_button_pressed(callback)`)
- Button press event detection

### Cross-Platform Development Support

The repository includes proxy implementations that allow for development on platforms other than Raspberry Pi:

- `proxydisplayhatmini.py`: Simulates the DisplayHATMini on macOS using Pygame
- `proxyunicornhatmini.py`: Simulates the UnicornHATMini on macOS using Pygame

## Example Applications

### Basic Examples

1. **`rainbow.py`**: Displays a concentric rainbow pattern that moves around the display
2. **`demo.py`**: Shows four different demoscene-style effects with transitions
3. **`buttons.py`**: Demonstrates basic button functionality with gpiozero
4. **`button-splash.py`**: Creates rainbow splash effects when buttons are pressed
5. **`colour-cycle.py`**: Cycles through hue values across all pixels
6. **`columns.py`**: A game where you stack columns of colored lights
7. **`forest-fire.py`**: Simulates tree growth and forest fires using cellular automata
8. **`fps.py`**: Shows the maximum refresh rate achievable on your Unicorn HAT Mini
9. **`image.py`**: Demonstrates scrolling an image across the display
10. **`simon.py`**: A memory game where you repeat color sequences
11. **`text.py`**: Scrolls text across the display with rainbow color effects

### Advanced Applications

1. **`rainbow-text-scroller.py`**: Scrolls multicolored text with interactive button controls
2. **`rainbow-pipe.py`**: Reads text from stdin to display on the HAT, useful for piping output from other commands
3. **`display-tester.py`**: Tests the display with various patterns
4. **`interactive-rectangle.py`**: Displays a rectangle that can be manipulated with buttons
5. **`sequence-commander.py`**: Trigger animations by entering button sequences (like cheat codes)

## Animation Framework

The repository includes a complete animation framework in the `animation/` directory:

### Core Animation Components

1. **`base.py`**: Defines the base Animation class and transition animations
2. **`registry.py`**: Implements a registry system for animations
3. **`sequencer.py`**: Controls the sequencing of animations with transitions
4. **`effects.py`**: Contains predefined animation effects (rainbow, spiral, rain, explosion, etc.)
5. **`games.py`**: Contains interactive game animations
6. **`scenes.py`**: A placeholder for scene-based animations

### Animation Player

- **`animations-sequencer.py`**: A script to load and run animation sequences from a configuration file
- **`config/animations.json`**: Configuration for animation sequences

## Pi Day 2025 Poster Tools

The `piday2025posters/` directory contains tools specifically designed for a Pi Day 2025 event:

1. **Display Utilities**:
   - `displayhatutils.py`: Utility functions for the Display HAT Mini
   - `display-tester.py`: Tests the Display HAT Mini
   - `display-image.py`: Displays a single image with transformation options

2. **Image Gallery**:
   - `image-gallery.py`: A feature-rich image gallery with slideshow capabilities
   - `display-hat-gallery.service`: Systemd service for auto-starting the gallery

3. **Transition Effects**:
   - `glitch.py`: Provides glitch transition effects between images
   - `ascii.py`: Provides ASCII art transition effects

4. **Automation**:
   - `startup-script.sh`: Script for starting the gallery at boot
   - `INSTALLATION.md`: Instructions for setting up the gallery to run at boot

## Common Patterns and Functionality

### Display Initialization Pattern

Most scripts follow this pattern:
```python
display = UnicornHATMini()
display.set_brightness(0.5)  # Set to reasonable brightness
```

### Button Handling

Scripts use one of two approaches for button handling:
1. **Polling approach**:
   ```python
   if display.read_button(display.BUTTON_A):
       # Handle button press
   ```

2. **Callback approach**:
   ```python
   def button_pressed(button):
       # Handle button press
   
   display.on_button_pressed(button_pressed)
   ```

### Main Loop Pattern

Most applications have a main loop like:
```python
try:
    while True:
        # Update display
        # Process buttons
        # Short delay to control refresh rate
        time.sleep(0.03)
except KeyboardInterrupt:
    # Clean up
    display.clear()
    display.show()
```

### Cross-Platform Compatibility

Many scripts include code to detect the platform and use the appropriate implementation:
```python
if platform.system() == "Darwin":  # macOS
    from proxydisplayhatmini import DisplayHATMini
else:  # Raspberry Pi
    from displayhatmini import DisplayHATMini
```

### Color Generation

Most animations use HSV color space for generating colorful effects:
```python
from colorsys import hsv_to_rgb
# ...
hue = (x + y) / float(width + height) + t * 0.2
r, g, b = [int(c * 255) for c in hsv_to_rgb(hue, 1.0, 1.0)]
```

## Installation and Setup

The repository includes installation scripts and documentation:

1. **Installation Scripts**:
   - `install.sh`: Main installation script
   - `install-bullseye.sh`: Installation script for Raspberry Pi OS Bullseye

2. **Setup Instructions**:
   - Enable SPI: `sudo raspi-config nonint do_spi 0`
   - Install the library: `sudo pip3 install unicornhatmini` or use the installation script
   - Various documentation files (README.md, REFERENCE.md, etc.)