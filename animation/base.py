#!/usr/bin/env python3
"""
Animation Base with Enhanced Debugging for Unicorn HAT Mini

This file provides enhanced versions of the animation base classes
with improved debugging output. To use these, replace or modify
your existing animation/base.py with this content.
"""

import time
import abc
import inspect


class Animation(abc.ABC):
    """Base class for all animations with enhanced debugging.
    
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
        self.debug_count = 0  # Frame counter for rate-limited debug output
        
        # Initialize from config
        self.name = self.config.get('name', self.__class__.__name__)
        self.duration = self.config.get('duration', 5.0)
        self.frame_rate = self.config.get('frame_rate', 30)
        self.frame_delay = 1.0 / self.frame_rate
        self.last_frame_time = 0
        
        # Debug control
        self.debug_level = self.config.get('debug_level', 1)  # 0=none, 1=basic, 2=verbose
        self.debug_frequency = self.config.get('debug_frequency', 30)  # Every Nth frame
        
        # Debug initialization
        print(f"[DEBUG] Created animation: {self.name} (duration: {self.duration}s)")
        if self.debug_level >= 2:
            # Print configuration details
            print(f"[DEBUG] Configuration: {self.config}")
            
    def setup(self):
        """Prepare the animation to run.
        
        This method is called once before the animation starts running.
        It should initialize any state needed by the animation.
        """
        self.start_time = time.time()
        self.last_frame_time = self.start_time
        self.is_running = True
        self.debug_count = 0
        
        # Debug setup
        print(f"\n[DEBUG] Starting animation: {self.name}")
        if self.debug_level >= 2:
            # Add more detailed setup information
            print(f"[DEBUG] Setup time: {time.strftime('%H:%M:%S')}")
            print(f"[DEBUG] Animation class: {self.__class__.__module__}.{self.__class__.__name__}")
    
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
        
        # Debug cleanup
        elapsed = time.time() - self.start_time
        print(f"[DEBUG] Ending animation: {self.name} (ran for {elapsed:.2f}s)")
    
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
            
        # Check if time is up for non-interactive animations
        if not self.config.get('interactive', False):
            elapsed = time.time() - self.start_time
            remaining = self.duration - elapsed
            is_done = elapsed > self.duration
            
            # Print remaining time occasionally
            if self.debug_level >= 1 and self.debug_count % self.debug_frequency == 0:
                print(f"[DEBUG] Animation: {self.name} - Time remaining: {remaining:.2f}s")
            
            return is_done
        
        # Interactive animations continue until explicitly finished
        return False
    
    def handle_button_press(self, button):
        """Handle a button press event.
        
        Args:
            button: The button that was pressed
            
        Returns:
            bool: True if the button press was handled, False otherwise
        """
        if self.debug_level >= 2:
            print(f"[DEBUG] {self.name} - Button press: {button} (not handled)")
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
            print(f"[DEBUG] Animation not running: {self.name}")
            return False
            
        # Increment debug frame counter
        self.debug_count += 1
        
        # Throttle frame rate and get elapsed time
        dt = self.throttle_frame_rate()
        
        # Output debugging information at specified frequency
        if self.debug_level >= 1 and self.debug_count % self.debug_frequency == 0:
            elapsed = time.time() - self.start_time
            fps = 1.0 / dt if dt > 0 else 0
            print(f"[DEBUG] Animation: {self.name} - Frame: {self.debug_count}, FPS: {fps:.1f}, Elapsed: {elapsed:.2f}s")
        
        # Add more detailed debug for verbose mode
        if self.debug_level >= 2 and self.debug_count % (self.debug_frequency * 5) == 0:
            # Add memory info or other stats in verbose mode
            print(f"[DEBUG] {self.name} - Detail: dt={dt:.4f}s")
        
        # Update animation state
        self.update(dt)
        
        # Render to display
        self.render()
        
        # Check if animation is finished
        if self.is_finished():
            if self.debug_level >= 1:
                print(f"[DEBUG] Animation finished: {self.name}")
            self.cleanup()
            return False
            
        return True


class TransitionAnimation(Animation):
    """Base class for transition animations with enhanced debugging.
    
    This class handles transitioning between two animations.
    """
    
    def __init__(self, display, config=None):
        """Initialize the transition.
        
        Args:
            display: The UnicornHATMini display
            config: Configuration dictionary with 'from_anim' and 'to_anim'
                    entries containing the animations to transition between
        """
        super().__init__(display, config)
        self.from_anim = self.config.get('from_anim')
        self.to_anim = self.config.get('to_anim')
        self.progress = 0.0
        
        # Enhanced debug for transitions
        if self.debug_level >= 1:
            from_name = self.from_anim.name if self.from_anim else "None"
            to_name = self.to_anim.name if self.to_anim else "None"
            print(f"[DEBUG] Creating transition: {from_name} → {to_name}")
        
    def is_finished(self):
        """Return True if the transition is complete."""
        return self.progress >= 1.0


class FadeTransition(TransitionAnimation):
    """Fade transition between two animations with enhanced debugging."""
    
    def update(self, dt):
        """Update the transition progress and render the blended frame."""
        self.display.clear()
        
        # Update progress (0.0 to 1.0)
        transition_duration = self.config.get('duration', 1.0)
        old_progress = self.progress
        self.progress = min(1.0, self.progress + dt / transition_duration)
        
        # Add transition-specific debug
        if self.debug_level >= 2 and self.debug_count % self.debug_frequency == 0:
            from_name = self.from_anim.name if self.from_anim else "None"
            to_name = self.to_anim.name if self.to_anim else "None"
            print(f"[DEBUG] Fade transition: {from_name} → {to_name}, Progress: {self.progress:.2f}")
        
        # TODO: Implement frame blending for smoother transitions
        # For now, just crossfade by showing one animation then the other
        if self.progress < 0.5:
            # First half of transition - show the from_anim
            if self.from_anim:
                # Track if we crossed the threshold
                if old_progress < 0.5 <= self.progress and self.debug_level >= 1:
                    print(f"[DEBUG] Transition halfway point: switching from {self.from_anim.name} to {self.to_anim.name}")
                
                self.from_anim.update(dt)
        else:
            # Second half of transition - show the to_anim
            if self.to_anim:
                self.to_anim.update(dt)