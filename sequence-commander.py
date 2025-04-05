#!/usr/bin/env python3
"""
Sequence Commander for Unicorn HAT Mini

A demo application that lets you trigger different animations by entering
button sequences, similar to cheat codes or combo moves in video games.

Available sequences:
- A, B, A, B: Triggers a spiral animation
- X, Y, X, Y: Triggers a rain animation
- A, X, B, Y: Triggers an explosion animation
- B, B, Y, Y: Triggers a snake animation
- Y, Y, Y, Y: Triggers a rainbow wave animation

Press and hold any button to show the help screen with available sequences.

Run with --animation flag to cycle through animations with any button press.
"""

import time
import random
import math
import colorsys
import argparse
import sys

try:
    # Try to import from the unicornhatutils wrapper first (which works on macOS too)
    from unicornhatutils import UnicornHATMini, display_info_message, clear_display
except ImportError:
    try:
        # Fall back to the direct library (Raspberry Pi only)
        from unicornhatmini import UnicornHATMini
        
        def display_info_message(display, message, submessage=""):
            display.clear()
            # Simple visual indicator since we can't display text
            for x in range(display.get_shape()[0]):
                display.set_pixel(x, 0, 255, 255, 255)
                display.set_pixel(x, display.get_shape()[1]-1, 255, 255, 255)
            display.show()
            time.sleep(1)
            
        def clear_display(display):
            display.clear()
            display.show()
    except ImportError:
        print("Error: Could not import UnicornHATMini. Please make sure the library is installed.")
        print("For Raspberry Pi: sudo pip3 install unicornhatmini")
        print("For development on macOS: Place unicornhatutils.py and proxyunicornhatmini.py in the same directory.")
        exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Sequence Commander for Unicorn HAT Mini')
    parser.add_argument('--brightness', '-b', type=float, default=0.5,
                       help='Display brightness from 0.0 to 1.0 (default: 0.5)')
    parser.add_argument('--duration', '-d', type=float, default=3.0,
                       help='Animation duration in seconds (default: 3.0)')
    parser.add_argument('--animation', '-a', action='store_true',
                       help='Animation mode: press any button to cycle through animations')
    return parser.parse_args()


class SequenceCommander:
    def __init__(self, display, animation_duration=3.0, animation_mode=False):
        self.display = display
        self.width, self.height = display.get_shape()
        self.animation_duration = animation_duration
        self.animation_mode = animation_mode
        
        # Define button names and pins
        self.buttons = {
            "A": display.BUTTON_A,
            "B": display.BUTTON_B,
            "X": display.BUTTON_X,
            "Y": display.BUTTON_Y
        }
        
        # Define the recognized sequences and their corresponding animations
        self.sequences = {
            "ABAB": self.spiral_animation,
            "XYXY": self.rain_animation,
            "AXBY": self.explosion_animation,
            "BBYY": self.snake_animation,
            "YYYY": self.rainbow_wave_animation
        }
        
        # Create a list of all animations for animation mode
        self.animations = [
            self.spiral_animation,
            self.rain_animation,
            self.explosion_animation,
            self.snake_animation, 
            self.rainbow_wave_animation
        ]
        self.current_animation_index = 0
        
        # Current input sequence
        self.current_sequence = ""
        self.sequence_timeout = None
        self.sequence_timeout_duration = 1.0  # seconds
        
        # Button state tracking
        self.button_states = {pin: False for pin in self.buttons.values()}
        self.button_press_times = {pin: 0 for pin in self.buttons.values()}
        
        # Animation state
        if self.animation_mode:
            # Start with the first animation in animation mode
            self.current_animation = self.animations[self.current_animation_index]
            self.animation_start_time = time.time()
            print(f"Starting in animation mode with animation 1/{len(self.animations)}")
        else:
            self.current_animation = None
            self.animation_start_time = None
        
        # Snake animation state
        self.snake_body = []
        self.snake_direction = (1, 0)  # Right
        self.snake_food = None

    def process_buttons(self):
        """Process button inputs and detect sequences."""
        long_press_detected = False
        button_handled = False
        
        for button_name, pin in self.buttons.items():
            # Get previous and current button state
            prev_state = self.button_states[pin]
            curr_state = self.display.read_button(pin)
            
            # Update button state
            self.button_states[pin] = curr_state
            
            # Handle long press (help screen)
            if curr_state:
                if self.button_press_times[pin] == 0:
                    self.button_press_times[pin] = time.time()
                elif time.time() - self.button_press_times[pin] > 1.0:
                    # Long press detected
                    long_press_detected = True
            else:
                # Handle button release
                if prev_state and not curr_state:  # Button was just released
                    press_duration = time.time() - self.button_press_times[pin]
                    if press_duration < 1.0:  # Short press
                        if self.animation_mode:
                            # In animation mode, any button press advances to next animation
                            self.current_animation_index = (self.current_animation_index + 1) % len(self.animations)
                            anim_func = self.animations[self.current_animation_index]
                            print(f"Button {button_name} pressed - switching to animation {self.current_animation_index + 1}/{len(self.animations)}")
                            self.trigger_animation(anim_func)
                            button_handled = True
                            break  # Exit loop once we've handled a button
                        else:
                            # Add to current sequence in sequence mode
                            self.current_sequence += button_name
                            print(f"Button {button_name} pressed - Current sequence: {self.current_sequence}")
                            
                            # Set timeout to clear the sequence if no new button is pressed
                            self.sequence_timeout = time.time() + self.sequence_timeout_duration
                            
                            # Check if the current sequence matches any known sequence
                            for seq, animation_func in self.sequences.items():
                                if self.current_sequence.endswith(seq):
                                    print(f"Sequence {seq} recognized! Triggering animation.")
                                    self.trigger_animation(animation_func)
                                    self.current_sequence = ""
                                    self.sequence_timeout = None
                                    break
                
                # Reset button timer on release
                self.button_press_times[pin] = 0
        
        # Skip sequence timeout check in animation mode if we handled a button
        if self.animation_mode and button_handled:
            return
            
        # Check for sequence timeout
        if self.sequence_timeout and time.time() > self.sequence_timeout:
            print(f"Sequence timeout - resetting sequence: {self.current_sequence}")
            self.current_sequence = ""
            self.sequence_timeout = None
        
        # Show help screen on long press
        if long_press_detected:
            self.show_help_screen()
            # Reset all button timers to prevent re-triggering
            for pin in self.buttons.values():
                self.button_press_times[pin] = time.time()
    
    def show_help_screen(self):
        """Show a help screen with available sequences."""
        print("Help screen displayed")
        
        # First we'll show a "?" pattern
        self.display.clear()
        
        # Draw a question mark (simplified for the small display)
        # Top curve
        for x in range(7, 11):
            self.display.set_pixel(x, 1, 255, 255, 255)
        self.display.set_pixel(6, 2, 255, 255, 255)
        self.display.set_pixel(11, 2, 255, 255, 255)
        self.display.set_pixel(11, 3, 255, 255, 255)
        self.display.set_pixel(10, 4, 255, 255, 255)
        self.display.set_pixel(9, 5, 255, 255, 255)
        self.display.set_pixel(9, 6, 255, 255, 255)
        
        self.display.show()
        time.sleep(1.0)
        
        if self.animation_mode:
            # In animation mode, show animation names
            animation_names = ["Spiral", "Rain", "Explosion", "Snake", "Rainbow"]
            for i, name in enumerate(animation_names):
                self.display.clear()
                # Flash a number for each animation
                number = i + 1
                x = self.width // 2
                y = self.height // 2
                
                # Draw a number in the center
                color = (255, 255, 255)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            self.display.set_pixel(nx, ny, *color)
                
                self.display.show()
                time.sleep(0.75)
        else:
            # In sequence mode, show the sequences
            for seq in self.sequences.keys():
                # Show sequence as button lights
                self.display.clear()
                for i, char in enumerate(seq):
                    x = 3 + i * 4
                    y = 3
                    color = {
                        'A': (255, 0, 0),    # Red
                        'B': (0, 255, 0),    # Green
                        'X': (0, 0, 255),    # Blue
                        'Y': (255, 255, 0)   # Yellow
                    }.get(char, (255, 255, 255))
                    
                    # Draw a 3x3 block for the button
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                self.display.set_pixel(nx, ny, *color)
                
                self.display.show()
                time.sleep(0.75)
            
        # Return to standby pulse or current animation
        if self.animation_mode:
            self.current_animation = self.animations[self.current_animation_index]
        else:
            self.current_animation = self.standby_pulse
        self.animation_start_time = time.time()
    
    def trigger_animation(self, animation_func):
        """Start a new animation."""
        self.current_animation = animation_func
        self.animation_start_time = time.time()
        # Initialize any animation-specific state
        if animation_func == self.snake_animation:
            # Initialize snake state
            self.snake_body = [(self.width // 2, self.height // 2)]
            self.snake_direction = (1, 0)  # Right
            self.place_food()
    
    def update(self):
        """Update the current state and display."""
        # Process button inputs
        self.process_buttons()
        
        # If an animation is running, check if it's finished
        if self.current_animation:
            if self.animation_start_time and time.time() - self.animation_start_time > self.animation_duration:
                # Animation timed out
                if self.animation_mode:
                    # In animation mode, only auto-cycle if it's not the snake animation
                    if self.current_animation != self.snake_animation:
                        self.current_animation_index = (self.current_animation_index + 1) % len(self.animations)
                        self.current_animation = self.animations[self.current_animation_index]
                        self.animation_start_time = time.time()
                        print(f"Auto-switching to animation {self.current_animation_index+1}/{len(self.animations)}")
                elif self.current_animation != self.snake_animation:
                    # In normal mode, return to standby pulse (except for snake)
                    self.current_animation = self.standby_pulse
                    self.animation_start_time = time.time()
            
            # Run the current animation
            self.current_animation()
        else:
            # Default animation when idle
            self.standby_pulse()
    
    def standby_pulse(self):
        """Subtle pulsing animation when in standby mode."""
        self.display.clear()
        
        # Calculate pulse intensity (0.0 to 1.0)
        intensity = (math.sin(time.time() * 2) + 1) / 2
        
        # Draw a subtle dot in the middle that pulses
        center_x, center_y = self.width // 2, self.height // 2
        
        for x in range(self.width):
            for y in range(self.height):
                # Calculate distance from center (normalized to 0.0-1.0)
                distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                max_distance = math.sqrt(center_x ** 2 + center_y ** 2)
                normalized_distance = distance / max_distance
                
                # Only light pixels close to the center based on the current intensity
                if normalized_distance < intensity * 0.35:
                    brightness = 1.0 - (normalized_distance / (intensity * 0.35))
                    hue = (time.time() / 10.0) % 1.0
                    r, g, b = [int(c * 255 * brightness) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                    self.display.set_pixel(x, y, r, g, b)
        
        self.display.show()
    
    def spiral_animation(self):
        """Draw a spiral animation."""
        self.display.clear()
        
        # Calculate animation progress (0.0 to 1.0)
        elapsed = time.time() - self.animation_start_time
        progress = min(1.0, elapsed / self.animation_duration)
        
        # Define spiral parameters
        max_radius = math.sqrt(self.width**2 + self.height**2) / 2
        center_x, center_y = self.width // 2, self.height // 2
        
        # Number of spiral arms
        num_arms = 2
        
        # Rotation speed
        rotation_speed = 2.0
        
        for x in range(self.width):
            for y in range(self.height):
                # Calculate polar coordinates
                dx, dy = x - center_x, y - center_y
                radius = math.sqrt(dx**2 + dy**2)
                if radius == 0:
                    radius = 0.001  # Avoid division by zero
                
                # Calculate angle in radians
                angle = math.atan2(dy, dx)
                
                # Spiral function: r = a + bθ
                # We want points where the radius is close to this function
                spiral_angle = (angle + elapsed * rotation_speed) % (2 * math.pi)
                spiral_r = progress * max_radius * spiral_angle / (2 * math.pi) * num_arms
                
                # Determine if this point is on the spiral
                if abs(radius - spiral_r % max_radius) < 1.0:
                    # Color based on angle
                    hue = (spiral_angle / (2 * math.pi) + elapsed / 2) % 1.0
                    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                    self.display.set_pixel(x, y, r, g, b)
        
        self.display.show()
    
    def rain_animation(self):
        """Simulate rain drops falling down the display."""
        self.display.clear()
        
        # Calculate animation progress (0.0 to 1.0)
        elapsed = time.time() - self.animation_start_time
        progress = min(1.0, elapsed / self.animation_duration)
        
        # Create raindrops
        num_drops = int(20 * progress) + 5
        
        for _ in range(num_drops):
            # Random x position
            x = random.randint(0, self.width - 1)
            
            # Calculate y position based on time and a random offset
            # This creates the illusion of drops falling at different speeds
            random_offset = random.uniform(0, 2 * math.pi)
            y_float = (elapsed * 5 + random_offset) % (self.height * 1.5)
            y = int(y_float) % self.height
            
            # Fade intensity based on position in animation
            intensity = 1.0
            if y_float >= self.height:
                # Fade out as drops "fall off" the bottom
                intensity = 1.0 - ((y_float - self.height) / (self.height * 0.5))
            
            # Blue color with varying intensity
            r, g, b = 0, 100 + int(155 * intensity), 200 + int(55 * intensity)
            self.display.set_pixel(x, y, r, g, b)
        
        self.display.show()
    
    def explosion_animation(self):
        """Create an explosion effect from the center outward."""
        self.display.clear()
        
        # Calculate animation progress (0.0 to 1.0)
        elapsed = time.time() - self.animation_start_time
        progress = min(1.0, elapsed / self.animation_duration)
        
        # Explosion parameters
        center_x, center_y = self.width // 2, self.height // 2
        max_radius = math.sqrt(self.width**2 + self.height**2) / 2
        current_radius = progress * max_radius
        ring_thickness = 2.0 * (1.0 - progress) + 0.5  # Ring gets thinner as it expands
        
        for x in range(self.width):
            for y in range(self.height):
                # Calculate distance from center
                distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # Check if the pixel is within the expanding ring
                if abs(distance - current_radius) < ring_thickness:
                    # Color based on angle and progress (shifts from yellow/orange to red)
                    angle = math.atan2(y - center_y, x - center_x)
                    hue = (0.05 - 0.05 * progress) % 1.0  # Shift from yellow (0.15) to red (0.0)
                    saturation = 1.0
                    brightness = 1.0
                    
                    # Add some variation based on angle
                    hue_variation = 0.05 * math.sin(angle * 5 + elapsed * 3)
                    hue = (hue + hue_variation) % 1.0
                    
                    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, saturation, brightness)]
                    self.display.set_pixel(x, y, r, g, b)
                
                # Also draw some "sparks" in the center
                elif distance < current_radius and random.random() < 0.05 * (1.0 - progress):
                    r, g, b = 255, 255, 100
                    self.display.set_pixel(x, y, r, g, b)
        
        self.display.show()
    
    def place_food(self):
        """Place a new food item for the snake at a random location."""
        if not self.snake_body:
            self.snake_food = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            return
            
        # Find an empty spot
        while True:
            food_pos = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if food_pos not in self.snake_body:
                self.snake_food = food_pos
                break
    
    def snake_animation(self):
        """Interactive snake game animation."""
        self.display.clear()
        
        # Snake moves every N frames
        move_interval = 0.2  # seconds
        
        # Check if it's time to update the snake position
        current_time = time.time()
        elapsed = current_time - self.animation_start_time
        frame_number = int(elapsed / move_interval)
        
        # Update snake position on new frames
        if frame_number > len(self.snake_body):
            # Get current head position
            head_x, head_y = self.snake_body[0]
            
            # Calculate new head position
            dx, dy = self.snake_direction
            new_head = ((head_x + dx) % self.width, (head_y + dy) % self.height)
            
            # Check if the snake hit itself
            if new_head in self.snake_body:
                # Game over - reset snake
                self.snake_body = [(self.width // 2, self.height // 2)]
                self.place_food()
            else:
                # Add new head
                self.snake_body.insert(0, new_head)
                
                # Check if snake ate the food
                if new_head == self.snake_food:
                    # Grow snake (don't remove tail)
                    self.place_food()
                    
                    # Check win condition (snake fills the screen)
                    if len(self.snake_body) >= self.width * self.height:
                        # Win animation - flash the display
                        for i in range(3):
                            for y in range(self.height):
                                for x in range(self.width):
                                    self.display.set_pixel(x, y, 0, 255, 0)
                            self.display.show()
                            time.sleep(0.2)
                            self.display.clear()
                            self.display.show()
                            time.sleep(0.2)
                        
                        # Reset snake
                        self.snake_body = [(self.width // 2, self.height // 2)]
                        self.place_food()
                else:
                    # Remove tail
                    self.snake_body.pop()
            
            # Update snake direction based on button presses
            if self.button_states.get(self.buttons["A"]):
                # Up
                self.snake_direction = (0, -1)
            elif self.button_states.get(self.buttons["B"]):
                # Left
                self.snake_direction = (-1, 0)
            elif self.button_states.get(self.buttons["X"]):
                # Down
                self.snake_direction = (0, 1)
            elif self.button_states.get(self.buttons["Y"]):
                # Right
                self.snake_direction = (1, 0)
        
        # Draw snake
        for i, (x, y) in enumerate(self.snake_body):
            # Head is white, body changes color
            if i == 0:
                self.display.set_pixel(x, y, 255, 255, 255)
            else:
                # Color cycles through green shades
                hue = 0.3  # Green
                saturation = 1.0
                brightness = 1.0 - (i / len(self.snake_body)) * 0.5
                r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, saturation, brightness)]
                self.display.set_pixel(x, y, r, g, b)
        
        # Draw food (red)
        if self.snake_food:
            food_x, food_y = self.snake_food
            # Make food pulsate
            brightness = (math.sin(current_time * 5) + 1) / 2
            r = 150 + int(105 * brightness)
            self.display.set_pixel(food_x, food_y, r, 0, 0)
        
        self.display.show()
    
    def rainbow_wave_animation(self):
        """Create a rainbow wave flowing across the display."""
        self.display.clear()
        
        # Calculate animation progress
        elapsed = time.time() - self.animation_start_time
        
        # Wave parameters
        freq = 0.3
        speed = 3.0
        
        for x in range(self.width):
            for y in range(self.height):
                # Calculate wave offset
                distance = (x + y) / (self.width + self.height)
                wave = math.sin(distance * 2 * math.pi * freq + elapsed * speed)
                
                # Map wave value (-1 to 1) to hue (0 to 1)
                hue = (wave + 1) / 2
                
                # Add time-based shift to make colors move
                hue = (hue + elapsed / 5.0) % 1.0
                
                r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                self.display.set_pixel(x, y, r, g, b)
        
        self.display.show()


def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize Unicorn HAT Mini
    display = UnicornHATMini()
    
    # Set brightness
    brightness = max(0.1, min(1.0, args.brightness))
    display.set_brightness(brightness)
    
    # Display startup message
    if args.animation:
        display_info_message(display, "Animation", "Mode")
    else:
        display_info_message(display, "Sequence", "Commander")
    time.sleep(1)
    
    # Create sequence commander
    commander = SequenceCommander(display, 
                                 animation_duration=args.duration,
                                 animation_mode=args.animation)
    
    try:
        # Main loop
        while True:
            commander.update()
            
            # Process events (needed for proxy implementation)
            if hasattr(display, 'process_events'):
                display.process_events()
            
            # Sleep to control frame rate
            time.sleep(0.05)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clean up
        clear_display(display)
        print("Display cleared")


if __name__ == "__main__":
    main()
