#!/usr/bin/env python3
"""
Animation Sequencer for Unicorn HAT Mini.

This script loads and runs a sequence of animations on the Unicorn HAT Mini.
"""

import os
import sys
import time
import argparse

# Determine if we're on Raspberry Pi or another platform
import platform
if platform.system() == "Darwin":  # macOS
    # Use the proxy implementation for development
    import sys
    sys.path.insert(0, os.path.abspath('.'))  # Add current directory to path
    try:
        # Try to import from the unicornhatutils wrapper
        from unicornhatutils import UnicornHATMini, display_info_message, clear_display
        print("Using proxy UnicornHATMini implementation for development")
    except ImportError:
        print("Error: Could not import UnicornHATMini proxy. Make sure unicornhatutils.py is in the same directory.")
        sys.exit(1)
else:  # Raspberry Pi or other Linux system
    try:
        # Try to import the real UnicornHATMini library
        from unicornhatmini import UnicornHATMini
        # Simple implementations of utility functions
        def display_info_message(display, message, submessage=""):
            display.clear()
            for x in range(display.get_shape()[0]):
                display.set_pixel(x, 0, 255, 255, 255)
            display.show()
            time.sleep(1)
            
        def clear_display(display):
            display.clear()
            display.show()
        print("Using actual UnicornHATMini implementation")
    except ImportError:
        print("Error: Could not import UnicornHATMini. Please install it with: sudo pip3 install unicornhatmini")
        sys.exit(1)

# Import our animation system
from animation import (
    Animation,
    register_animation,
    get_animation_names,
    discover_animations,
    AnimationSequencer
)

# Import animation modules - this will register animations via decorators
import animation.effects
import animation.scenes
import animation.games


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Animation Sequencer for Unicorn HAT Mini')
    
    parser.add_argument('--config', '-c', type=str, default='config/animations.json',
                        help='Path to animation configuration file')
    
    parser.add_argument('--brightness', '-b', type=float, default=0.8,
                        help='Display brightness (0.0-1.0, default: 0.8)')
    
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available animations and exit')
    
    parser.add_argument('--animation', '-a', type=str,
                        help='Run a specific animation')
    
    parser.add_argument('--rotation', '-r', type=int, choices=[0, 90, 180, 270], default=0,
                        help='Display rotation (0, 90, 180, or 270 degrees)')
    
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Enable interactive mode (buttons control animations)')
    
    return parser.parse_args()


def list_animations():
    """List all available animations."""
    print("Available animations:")
    for name in get_animation_names():
        print(f"  - {name}")


def setup_button_handlers(sequencer, display):
    """Set up button handlers for interactive mode."""
    
    # Define button handlers
    def button_a_handler():
        """Button A: Previous animation."""
        print("Button A pressed: Previous animation")
        sequencer.previous()
    
    def button_b_handler():
        """Button B: Toggle pause/resume."""
        if sequencer.is_paused:
            print("Button B pressed: Resume")
            sequencer.resume()
        else:
            print("Button B pressed: Pause")
            sequencer.pause()
    
    def button_x_handler():
        """Button X: Next animation."""
        print("Button X pressed: Next animation")
        sequencer.next()
    
    def button_y_handler():
        """Button Y: Show animation info."""
        current_anim = sequencer.current_animation
        if current_anim:
            name = current_anim.name
            elapsed = time.time() - current_anim.start_time
            duration = current_anim.duration
            print(f"Current animation: {name}")
            print(f"Elapsed time: {elapsed:.1f}s / {duration:.1f}s")
            # Show status on display
            display_info_message(display, name, f"{int(elapsed)}/{int(duration)}s")
    
    # Register button handlers
    sequencer.register_button_handler(display.BUTTON_A, button_a_handler)
    sequencer.register_button_handler(display.BUTTON_B, button_b_handler)
    sequencer.register_button_handler(display.BUTTON_X, button_x_handler)
    sequencer.register_button_handler(display.BUTTON_Y, button_y_handler)

def display_menu(display, options, selected_index):
    """Display the menu on the Unicorn HAT Mini."""
    display.clear()
    
    for i, option in enumerate(options):
        if i == selected_index:
            color = (255, 255, 255)  # White for selected option
        else:
            color = (128, 128, 128)  # Gray for unselected options
        
        # Draw a simple rectangle for each option
        y = i * 2
        display.set_pixel(0, y, *color)
        display.set_pixel(0, y + 1, *color)
        display.set_pixel(1, y, *color)
        display.set_pixel(1, y + 1, *color)
    
    display.show()

def run_menu(display, sequencer):
    """Run the animation selection menu."""
    options = get_animation_names()
    selected_index = 0
    
    while True:
        display_menu(display, options, selected_index)
        
        # Wait for button press
        while True:
            if display.read_button(display.BUTTON_A):
                # Previous option
                selected_index = (selected_index - 1) % len(options)
                break
            elif display.read_button(display.BUTTON_B):
                # Next option
                selected_index = (selected_index + 1) % len(options)
                break
            elif display.read_button(display.BUTTON_X):
                # Run the selected animation
                sequencer.jump_to(selected_index)
                sequencer.start()
                return
            elif display.read_button(display.BUTTON_Y):
                # Quit the menu
                return
            
            time.sleep(0.1)



def handle_button_presses(display, sequencer):
    """Handle button presses and pass them to the sequencer."""
    buttons = [
        display.BUTTON_A,
        display.BUTTON_B,
        display.BUTTON_X,
        display.BUTTON_Y
    ]
    
    button_names = {
        display.BUTTON_A: "A",
        display.BUTTON_B: "B",
        display.BUTTON_X: "X",
        display.BUTTON_Y: "Y"
    }
    
    # Track previous button states
    prev_states = {button: False for button in buttons}
    
    # Read current button states
    curr_states = {button: display.read_button(button) for button in buttons}
    
    # Check for button presses (transitions from not pressed to pressed)
    for button in buttons:
        if curr_states[button] and not prev_states[button]:
            # Button was just pressed
            print(f"Button {button_names.get(button, button)} pressed")
            sequencer.handle_button_press(button)
    
    # Update previous states
    for button in buttons:
        prev_states[button] = curr_states[button]


def main():
    """Main function."""
    args = parse_arguments()
    
    # List animations if requested
    if args.list:
        list_animations()
        return
    
    # Initialize the display
    display = UnicornHATMini()
    display.set_rotation(args.rotation)
    display.set_brightness(args.brightness)
    
    # Show startup message
    display_info_message(display, "Starting", "Animation Sequencer")
    
    # Create animation sequencer
    config_file = args.config if os.path.exists(args.config) else None
    sequencer = AnimationSequencer(display, config_file)
    
    if args.interactive:
        # Set up button handlers
        setup_button_handlers(sequencer, display)
    
    # Run a specific animation if requested
    if args.animation:
        # Check if the animation exists
        available_animations = get_animation_names()
        if args.animation in available_animations:
            # Find the index of the animation
            for i, anim in enumerate(sequencer.animations):
                if anim.__class__.__name__ == args.animation:
                    sequencer.jump_to(i)
                    break
        else:
            print(f"Animation '{args.animation}' not found.")
            print("Available animations:")
            for name in available_animations:
                print(f"  - {name}")
            return
    
    try:
        # Start the animation sequence
        # sequencer.start()
        # Show the animation selection menu
        run_menu(display, sequencer)
        
        # Main loop
        while True:
            # Update the animation sequencer
            if not sequencer.update():
                break
            
            # Handle button presses if interactive
            if args.interactive:
                handle_button_presses(display, sequencer)
            
            # Process display events if available
            if hasattr(display, 'process_events'):
                display.process_events()
            
            # Short delay to prevent CPU hogging
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
    finally:
        # Clean up
        clear_display(display)


if __name__ == "__main__":
    main()