#!/usr/bin/env python3
"""
Test script for debugging the animation sequencer.
This simple script creates a single test animation and runs it with debugging enabled.
"""

import time
import colorsys
import argparse

try:
    # Try to import from the unicornhatutils wrapper first (which works on macOS too)
    from unicornhatutils import UnicornHATMini
except ImportError:
    try:
        # Fall back to the direct library (Raspberry Pi only)
        from unicornhatmini import UnicornHATMini
    except ImportError:
        print("Error: Could not import UnicornHATMini.")
        exit(1)


class TestAnimation:
    """Simple test animation with debug output."""
    
    def __init__(self, display, name="TestAnimation", duration=5.0, debug_level=1):
        """Initialize the test animation."""
        self.display = display
        self.width, self.height = display.get_shape()
        self.name = name
        self.duration = duration
        self.debug_level = debug_level
        self.start_time = None
        self.frame_count = 0
        
        print(f"[DEBUG] Created animation: {self.name} (duration: {self.duration}s)")
    
    def setup(self):
        """Set up the animation."""
        self.start_time = time.time()
        self.frame_count = 0
        print(f"\n[DEBUG] Starting animation: {self.name}")
    
    def update(self):
        """Update the animation."""
        self.frame_count += 1
        
        # Clear the display
        self.display.clear()
        
        # Draw a rainbow pattern
        t = time.time() - self.start_time
        
        for y in range(self.height):
            for x in range(self.width):
                # Calculate hue based on position and time
                hue = (x + y) / float(self.width + self.height) + t * 0.2
                hue = hue % 1.0
                
                # Convert HSV to RGB
                r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                
                # Set the pixel
                self.display.set_pixel(x, y, r, g, b)
        
        # Show the display
        self.display.show()
        
        # Log animation progress at regular intervals
        if self.frame_count % 30 == 0:
            elapsed = time.time() - self.start_time
            remaining = self.duration - elapsed
            
            print(f"[DEBUG] Animation: {self.name} - Frame: {self.frame_count}")
            print(f"[DEBUG] Elapsed: {elapsed:.2f}s, Remaining: {remaining:.2f}s")
            
            if self.debug_level >= 2:
                print(f"[DEBUG] Animation details: Test animation drawing rainbow pattern")
        
        # Check if animation is done
        if elapsed >= self.duration:
            print(f"[DEBUG] Animation finished: {self.name}")
            return False
        
        return True
    
    def run(self):
        """Run the animation until it completes."""
        self.setup()
        
        try:
            while self.update():
                time.sleep(1.0 / 30.0)  # 30 FPS
                
                # Process events if available (for proxy implementation)
                if hasattr(self.display, 'process_events'):
                    self.display.process_events()
        
        except KeyboardInterrupt:
            print("\nAnimation interrupted")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test Animation Debugging')
    
    parser.add_argument('--brightness', '-b', type=float, default=0.5,
                        help='Display brightness (0.0-1.0)')
    
    parser.add_argument('--duration', '-t', type=float, default=10.0,
                        help='Animation duration in seconds')
    
    parser.add_argument('--debug', '-d', type=int, choices=[0, 1, 2], default=1,
                        help='Debug level: 0=none, 1=basic, 2=verbose')
    
    args = parser.parse_args()
    
    # Initialize display
    display = UnicornHATMini()
    display.set_brightness(args.brightness)
    
    print(f"Starting test with debug level {args.debug}")
    
    # Create and run test animation
    animation = TestAnimation(
        display, 
        name="RainbowTest",
        duration=args.duration,
        debug_level=args.debug
    )
    
    animation.run()
    
    # Clear display
    display.clear()
    display.show()
    
    print("Test complete")


if __name__ == "__main__":
    main()
