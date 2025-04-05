#!/usr/bin/env python3
"""
Base class for all Unicorn HAT Mini animations.

This module defines the Animation base class that all animations must inherit from
to work with the animation sequencer system.
"""

import time
import abc


class Animation(abc.ABC):
    """Base class for all animations.
    
    This abstract class defines the interface that all animations must implement
    to work with the animation sequencer system.
    """
    
    def __init__(self, display, config=None):
        """Initialize the animation.
        
        Args:
            display: The UnicornHATMini display object
            config: Optional configuration dictionary
        """
        self.display = display
        self.config = config or {}
        self.width, self.height = display.get_shape()
        self.start_time = None
        self.is_running = False
        
        # Initialize from config
        self.name = self.config.get('name', self.__class__.__name__)
        self.duration = self.config.get('duration', 5.0)
        self.frame_rate = self.config.get('frame_rate', 30)
        self.frame_delay = 1.0 / self.frame_rate
        self.last_frame_time = 0
        
    def setup(self):
        """Prepare the animation to run.
        
        This method is called once before the animation starts running.
        It should initialize any state needed by the animation.
        """
        self.start_time = time.time()
        self.last_frame_time = self.start_time
        self.is_running = True
    
    @abc.abstractmethod
    def update(self, dt):
        """Update the animation state and render one frame.
        
        This method is called once per frame while the animation is running.
        It should update the animation state and render to the display.
        
        Args:
            dt: Time in seconds since the last update
        """
        pass
    
    def render(self):
        """Render the current state to the display.
        
        By default, just calls display.show(), but animations
        can override this if needed.
        """
        self.display.show()
    
    def cleanup(self):
        """Clean up resources used by the animation.
        
        This method is called once after the animation is finished.
        It should release any resources allocated by the animation.
        """
        self.is_running = False
    
    def is_finished(self):
        """Return True if the animation has completed.
        
        By default, animations finish after their duration has elapsed.
        Interactive animations can override this to continue until an
        event occurs.
        
        Returns:
            bool: True if the animation is finished
        """
        if self.start_time is None:
            return True
            
        # Non-interactive animations end after their duration
        if not self.config.get('interactive', False):
            return time.time() - self.start_time > self.duration
        
        # Interactive animations continue until explicitly finished
        return False
    
    def handle_button_press(self, button):
        """Handle a button press event.
        
        Args:
            button: The button that was pressed
            
        Returns:
            bool: True if the button press was handled, False otherwise
        """
        return False
    
    def throttle_frame_rate(self):
        """Throttle the frame rate to the configured value.
        
        Returns:
            float: Time in seconds since the last frame
        """
        current_time = time.time()
        dt = current_time - self.last_frame_time
        
        # Wait until it's time for the next frame
        time_to_next_frame = self.frame_delay - dt
        if time_to_next_frame > 0:
            time.sleep(time_to_next_frame)
            current_time = time.time()
            dt = current_time - self.last_frame_time
            
        self.last_frame_time = current_time
        return dt
    
    def run_frame(self):
        """Run a single frame of the animation.
        
        Returns:
            bool: True if the animation is still running, False if finished
        """
        if not self.is_running:
            print("Animation not running")
            return False
            
        # Throttle frame rate and get elapsed time
        dt = self.throttle_frame_rate()
        print(f"Frame dt: {dt:.4f}s")
        
        # Update animation state
        self.update(dt)
        
        # Render to display
        self.render()
        print("Frame rendered")
        
        # Check if animation is finished
        if self.is_finished():
            print("Animation finished")
            self.cleanup()
            return False
            
        return True