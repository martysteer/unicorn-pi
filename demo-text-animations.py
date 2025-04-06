#!/usr/bin/env python3
"""
Demo for Text Animations on Unicorn HAT Mini

This script demonstrates various text animations available in the animation framework.
It shows examples of both the base TextAnimation and the StaticTextAnimation classes.

Usage:
  python demo-text-animations.py --text "Hello" --duration 15

Button Controls:
  - Button A: Change text position (top, center, bottom)
  - Button B: Change color mode (static, rainbow, pulse)
  - Button X: Toggle between animation types
  - Button Y: Exit the demo
"""

import time
import argparse
import sys
import os

# Ensure the animation module is in the Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    # Try to import from the unicornhatutils wrapper first (which works on macOS too)
    from unicornhatutils import UnicornHATMini, display_info_message, clear_display
except ImportError:
    try:
        # Fall back to the direct library (Raspberry Pi only)
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
        print("Error: Could not import UnicornHATMini.")
        print("Please install it with: sudo pip3 install unicornhatmini")
        print("Or place unicornhatutils.py in the same directory.")
        sys.exit(1)

try:
    # Import our text animations
    from animation.text import TextAnimation, StaticTextAnimation
except ImportError:
    print("Error: Could not import TextAnimation.")
    print("Make sure animation/text.py exists and is correctly implemented.")
    print("Current directory:", os.getcwd())
    print("Python path:", sys.path)
    sys.exit(1)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Demo Text Animations for Unicorn HAT Mini')
    
    parser.add_argument('--text', type=str, default='Hello',
                       help='Text to display (default: Hello)')
    
    parser.add_argument('--brightness', '-b', type=float, default=0.5,
                       help='Display brightness (0.0-1.0, default: 0.5)')
    
    parser.add_argument('--duration', '-d', type=float, default=30.0,
                       help='Demo duration in seconds (default: 30.0)')
    
    return parser.parse_args()


class TextAnimationDemo:
    """Demo class for text animations."""
    
    def __init__(self, display, text="Hello", duration=30.0):
        """Initialize the text animation demo."""
        self.display = display
        self.text = text
        self.duration = duration
        self.width, self.height = display.get_shape()
        
        # Current settings
        self.current_position = "center"
        self.current_color_mode = "rainbow"
        self.current_animation_type = "StaticTextAnimation"
        
        # Available options
        self.positions = ["top", "center", "bottom"]
        self.color_modes = ["static", "rainbow", "pulse"]
        self.animation_types = ["StaticTextAnimation", "TextAnimation"]
        
        # Current animation
        self.animation = None
        
        # Button state tracking
        self.prev_button_states = {
            self.display.BUTTON_A: False,
            self.display.BUTTON_B: False,
            self.display.BUTTON_X: False,
            self.display.BUTTON_Y: False
        }
    
    def create_animation(self):
        """Create an animation with current settings."""
        # Create configuration
        config = {
            'text': self.text,
            'position': self.current_position,
            'color_mode': self.current_color_mode,
            'duration': self.duration,
            'use_custom_font': True
        }
        
        # Create the appropriate animation type
        if self.current_animation_type == "StaticTextAnimation":
            self.animation = StaticTextAnimation(self.display, config)
        else:
            self.animation = TextAnimation(self.display, config)
        
        # Set up the animation
        self.animation.setup()
        
        print(f"Created {self.current_animation_type} with: position={self.current_position}, color_mode={self.current_color_mode}")
    
    def handle_buttons(self):
        """Check for button presses and handle accordingly."""
        # Read current button states
        curr_a = self.display.read_button(self.display.BUTTON_A)
        curr_b = self.display.read_button(self.display.BUTTON_B)
        curr_x = self.display.read_button(self.display.BUTTON_X)
        curr_y = self.display.read_button(self.display.BUTTON_Y)
        
        # Check for button presses (transitions from not pressed to pressed)
        if curr_a and not self.prev_button_states[self.display.BUTTON_A]:
            # Button A: Change position
            idx = self.positions.index(self.current_position)
            idx = (idx + 1) % len(self.positions)
            self.current_position = self.positions[idx]
            
            # Recreate animation with new settings
            self.create_animation()
        
        if curr_b and not self.prev_button_states[self.display.BUTTON_B]:
            # Button B: Change color mode
            idx = self.color_modes.index(self.current_color_mode)
            idx = (idx + 1) % len(self.color_modes)
            self.current_color_mode = self.color_modes[idx]
            
            # Recreate animation with new settings
            self.create_animation()
        
        if curr_x and not self.prev_button_states[self.display.BUTTON_X]:
            # Button X: Toggle animation type
            idx = self.animation_types.index(self.current_animation_type)
            idx = (idx + 1) % len(self.animation_types)
            self.current_animation_type = self.animation_types[idx]
            
            # Recreate animation with new settings
            self.create_animation()
        
        if curr_y and not self.prev_button_states[self.display.BUTTON_Y]:
            # Button Y: Exit demo
            return False
        
        # Update previous button states
        self.prev_button_states[self.display.BUTTON_A] = curr_a
        self.prev_button_states[self.display.BUTTON_B] = curr_b
        self.prev_button_states[self.display.BUTTON_X] = curr_x
        self.prev_button_states[self.display.BUTTON_Y] = curr_y
        
        return True
    
    def run(self):
        """Run the text animation demo."""
        # Create initial animation
        self.create_animation()
        
        # Start time
        start_time = time.time()
        
        # Main loop
        try:
            print("Demo running... Press Ctrl+C to exit")
            print("Button controls:")
            print("  A: Change position (top, center, bottom)")
            print("  B: Change color mode (static, rainbow, pulse)")
            print("  X: Toggle animation type")
            print("  Y: Exit the demo")
            
            while time.time() - start_time < self.duration:
                # Calculate delta time
                dt = 1.0 / 30.0  # Fixed for demo
                
                # Handle button presses
                if not self.handle_buttons():
                    print("Exiting demo due to button press")
                    break
                
                # Update the animation
                self.animation.update(dt)
                
                # Process events (needed for proxy implementation)
                if hasattr(self.display, 'process_events'):
                    self.display.process_events()
                
                # Sleep to control frame rate
                time.sleep(1.0 / 30.0)
        
        except KeyboardInterrupt:
            print("\nDemo interrupted")
        
        # Clean up
        clear_display(self.display)
        print("Demo complete")


def main():
    """Main function to run the text animation demo."""
    args = parse_arguments()
    
    # Initialize the display
    display = UnicornHATMini()
    display.set_brightness(args.brightness)
    
    # Show welcome message
    display_info_message(display, "Text", "Animation Demo")
    time.sleep(1)
    
    # Create and run the demo
    demo = TextAnimationDemo(
        display=display,
        text=args.text,
        duration=args.duration
    )
    
    demo.run()


if __name__ == "__main__":
    main()
