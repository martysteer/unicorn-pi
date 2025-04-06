import sys
import time

try:
    from unicornhatmini import UnicornHATMini
except ImportError:
    from unicornhatutils import UnicornHATMini

# Initialize the display
display = UnicornHATMini()
display.set_brightness(0.5)
display.clear()

# Define the bitmap font (5x7 ASCII font)
font = {
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
    '"': [0x00, 0x07, 0x00, 0x07, 0x00],
    '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
    # ... add more characters as needed
}

def render_char(char, x, y, color=(255, 255, 255)):
    """Render a character at the specified position."""
    bitmap = font.get(char.upper(), [])
    for row in range(len(bitmap)):
        for col in range(5):
            if bitmap[row] & (1 << (4 - col)):
                display.set_pixel(x + col, y + row, *color)

def clear_display():
    """Clear the display."""
    display.clear()
    display.show()

def main():
    """Main function to run the typewriter script."""
    x, y = 0, 0
    color = (255, 255, 255)  # White text color

    try:
        while True:
            char = sys.stdin.read(1)
            if char == '\n':
                # Handle line breaks
                x = 0
                y += 8
                if y >= display.HEIGHT:
                    y = 0
                    clear_display()
            elif char == '\b':
                # Handle backspace
                if x > 0:
                    x -= 6
                    if x < 0:
                        x = display.WIDTH - 6
                        y -= 8
                        if y < 0:
                            y = display.HEIGHT - 8
                    for i in range(5):
                        for j in range(7):
                            display.set_pixel(x + i, y + j, 0, 0, 0)
            else:
                # Render the character on the display
                render_char(char, x, y, color)
                x += 6
                if x >= display.WIDTH:
                    x = 0
                    y += 8
                    if y >= display.HEIGHT:
                        y = 0
                        clear_display()
            display.show()
    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C)
        clear_display()

if __name__ == '__main__':
    main()
