# Unicorn HAT Mini Examples

This guide provides instructions for running each example in the Unicorn HAT Mini Python library.

## Prerequisites

Before running any examples:

1. Make sure you've installed the Unicorn HAT Mini library:
   ```bash
   sudo pip3 install unicornhatmini
   ```
   
   Or if you prefer to install from source:
   ```bash
   git clone https://github.com/pimoroni/unicornhatmini-python
   cd unicornhatmini-python
   sudo ./install.sh
   ```

2. Enable SPI on your Raspberry Pi:
   ```bash
   sudo raspi-config nonint do_spi 0
   ```

3. The examples are typically copied to `~/Pimoroni/unicornhatmini/examples/` during installation if you selected 'y' during the install script.

## Running the Examples

Navigate to the examples directory:

```bash
cd ~/Pimoroni/unicornhatmini/examples/
```

### Rainbow Example
Displays a concentric rainbow pattern that moves around the display:
```bash
python3 rainbow.py
```

### Demo Example
Shows four different demoscene-style effects with transitions between them:
```bash
python3 demo.py
```

### Buttons Example
Demonstrates basic button functionality with GPIOZero:
```bash
python3 buttons.py
```

### Button Splash Example
Creates a rainbow splash effect when buttons are pressed:
```bash
python3 button-splash.py
```

### Colour Cycle Example
Cycles through hue values across all pixels:
```bash
python3 colour-cycle.py
```

### Columns Example
A simple game where you stack columns of colored lights:
```bash
python3 columns.py
```

### Forest Fire Example
Simulates tree growth and forest fires using cellular automata:
```bash
python3 forest-fire.py
```

### FPS Example
Shows the maximum refresh rate of your Unicorn HAT Mini:
```bash
python3 fps.py
```

### Image Example
Demonstrates scrolling an image across the display:
```bash
python3 image.py
```
Note: This requires the "twister.png" file to be in the same directory.

### Simon Example
A memory game where you repeat color sequences:
```bash
python3 simon.py
```

### Text Example
Scrolls text across the display with a rainbow color effect:
```bash
python3 text.py
```
Note: This requires the "5x7.ttf" font file to be in the same directory.

## Display Rotation

Many examples support screen rotation. You can specify a rotation angle (0, 90, 180, or 270 degrees) as a command-line parameter:

```bash
python3 image.py 90
```

## Adjusting Brightness

All examples set a default brightness (typically 0.1 or 0.5 on a scale of 0-1) that's safe for viewing. You can modify the brightness in the code if needed, but be careful as full brightness can be very intense!

## Exiting Examples

Press Ctrl+C to exit any of the running examples.

## Troubleshooting

If you encounter issues:

1. Make sure SPI is enabled: `sudo raspi-config nonint do_spi 0`
2. Ensure you're using Python 3: `python3 example.py` not `python example.py`
3. Verify the Unicorn HAT Mini is seated correctly on your Raspberry Pi
4. Check that you have the latest library version: `sudo pip3 install --upgrade unicornhatmini`
