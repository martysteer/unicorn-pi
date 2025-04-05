#!/usr/bin/env python3
"""
Animation sequencer for Unicorn HAT Mini animations.

This module provides the AnimationSequencer class that manages a sequence of animations,
handles transitions, and provides playback control.
"""

import time
import json
import random

from .base import Animation
from .registry import create_animation, get_animation_names


class TransitionAnimation(Animation):
    """Base class for transition animations.
    
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
        
    def is_finished(self):
        """Return True if the transition is complete."""
        return self.progress >= 1.0


class FadeTransition(TransitionAnimation):
    """Fade transition between two animations."""
    
    def update(self, dt):
        """Update the transition progress and render the blended frame."""
        self.display.clear()
        
        # Update progress (0.0 to 1.0)
        transition_duration = self.config.get('duration', 1.0)
        self.progress = min(1.0, self.progress + dt / transition_duration)
        
        # TODO: Implement frame blending for smoother transitions
        # For now, just crossfade by showing one animation then the other
        if self.progress < 0.5:
            # First half of transition - show the from_anim
            if self.from_anim:
                self.from_anim.update(dt)
        else:
            # Second half of transition - show the to_anim
            if self.to_anim:
                self.to_anim.update(dt)


class AnimationSequencer:
    """Manages a sequence of animations with transitions."""
    
    def __init__(self, display, config_file=None):
        """Initialize the animation sequencer.
        
        Args:
            display: The UnicornHATMini display
            config_file: Optional path to a configuration file
        """
        self.display = display
        self.animations = []
        self.current_index = 0
        self.current_animation = None
        self.next_animation = None
        self.transition = None
        self.is_transitioning = False
        self.is_running = False
        self.is_paused = False
        self.button_handlers = {}
        
        # Load configuration
        self.config = self._load_config(config_file)
        self._init_animations()
        
    def _load_config(self, config_file):
        """Load the animation sequence configuration.
        
        Args:
            config_file: Path to a JSON configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            'animations': [],
            'transition': 'fade',
            'transition_duration': 1.0,
            'loop': True,
            'shuffle': False,
            'default_duration': 5.0
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading config file: {e}")
        
        return default_config
    
    def _init_animations(self):
        """Initialize animations from config."""
        animation_configs = self.config.get('animations', [])
        
        if not animation_configs:
            # If no animations in config, use all available animations
            for name in get_animation_names():
                animation_configs.append({
                    'name': name,
                    'duration': self.config.get('default_duration', 5.0)
                })
        
        # Create animation objects
        for anim_config in animation_configs:
            name = anim_config.get('name')
            if name:
                anim = create_animation(name, self.display, anim_config)
                if anim:
                    self.animations.append(anim)
        
        if self.config.get('shuffle', False):
            random.shuffle(self.animations)
        
        # Initialize the first animation
        if self.animations:
            self.current_animation = self.animations[0]
            self.current_animation.setup()
    
    def _create_transition(self, from_anim, to_anim):
        """Create a transition animation between two animations.
        
        Args:
            from_anim: The animation to transition from
            to_anim: The animation to transition to
            
        Returns:
            A transition animation
        """
        transition_type = self.config.get('transition', 'fade')
        transition_duration = self.config.get('transition_duration', 1.0)
        
        transition_config = {
            'from_anim': from_anim,
            'to_anim': to_anim,
            'duration': transition_duration
        }
        
        # TODO: Support more transition types
        return FadeTransition(self.display, transition_config)
    
    def next(self):
        """Advance to the next animation."""
        if not self.animations:
            return
            
        # If we're already transitioning, do nothing
        if self.is_transitioning:
            return
            
        # Determine the next animation
        next_index = (self.current_index + 1) % len(self.animations)
        
        # If we've reached the end and not looping, stop
        if next_index == 0 and not self.config.get('loop', True):
            self.current_animation.cleanup()
            self.current_animation = None
            self.is_running = False
            return
            
        self.current_index = next_index
        self.next_animation = self.animations[next_index]
        self.next_animation.setup()
        
        # Create transition
        self.transition = self._create_transition(
            self.current_animation, 
            self.next_animation
        )
        self.transition.setup()
        self.is_transitioning = True
    
    def previous(self):
        """Go back to the previous animation."""
        if not self.animations:
            return
            
        # If we're already transitioning, do nothing
        if self.is_transitioning:
            return
            
        # Determine the previous animation
        prev_index = (self.current_index - 1) % len(self.animations)
        self.current_index = prev_index
        self.next_animation = self.animations[prev_index]
        self.next_animation.setup()
        
        # Create transition
        self.transition = self._create_transition(
            self.current_animation, 
            self.next_animation
        )
        self.transition.setup()
        self.is_transitioning = True
    
    def jump_to(self, index):
        """Jump to a specific animation by index."""
        if not self.animations or index < 0 or index >= len(self.animations):
            return
            
        # If we're already transitioning, do nothing
        if self.is_transitioning:
            return
            
        self.current_index = index
        self.next_animation = self.animations[index]
        self.next_animation.setup()
        
        # Create transition
        self.transition = self._create_transition(
            self.current_animation, 
            self.next_animation
        )
        self.transition.setup()
        self.is_transitioning = True
    
    def handle_button_press(self, button):
        """Handle a button press event.
        
        Args:
            button: The button that was pressed
            
        Returns:
            bool: True if the button press was handled, False otherwise
        """
        # First, check if the current animation handles this button
        if self.current_animation and self.current_animation.handle_button_press(button):
            return True
            
        # Then check if we have a handler for this button
        handler = self.button_handlers.get(button)
        if handler:
            handler()
            return True
            
        return False
    
    def register_button_handler(self, button, handler):
        """Register a handler for a button press.
        
        Args:
            button: The button to handle
            handler: Function to call when the button is pressed
        """
        self.button_handlers[button] = handler
    
    def start(self):
        """Start the animation sequence."""
        if not self.animations:
            return
            
        self.is_running = True
        self.is_paused = False
        
        if not self.current_animation:
            self.current_animation = self.animations[0]
            self.current_animation.setup()
    
    def stop(self):
        """Stop the animation sequence."""
        self.is_running = False
        
        if self.current_animation:
            self.current_animation.cleanup()
            self.current_animation = None
            
        if self.transition:
            self.transition.cleanup()
            self.transition = None
            
        self.is_transitioning = False
    
    def pause(self):
        """Pause the animation sequence."""
        self.is_paused = True
    
    def resume(self):
        """Resume the animation sequence."""
        self.is_paused = False
    
    def update(self):
        """Update the current animation or transition.
        
        Returns:
            bool: True if the animation sequence is still running
        """
        if not self.is_running or self.is_paused:
            return self.is_running
            
        if self.is_transitioning:
            # Update the transition
            if self.transition.run_frame():
                # Transition still in progress
                return True
                
            # Transition finished, switch to next animation
            self.transition.cleanup()
            self.transition = None
            self.is_transitioning = False
            
            if self.current_animation:
                self.current_animation.cleanup()
                
            self.current_animation = self.next_animation
            self.next_animation = None
            
            return True
        
        elif self.current_animation:
            # Update the current animation
            if self.current_animation.run_frame():
                # Animation still running
                return True
                
            # Animation finished, move to next
            self.next()
            return True
            
        return False
    
    def run(self):
        """Run the animation sequence until stopped."""
        self.start()
        
        try:
            while self.update():
                # Process display events if available
                if hasattr(self.display, 'process_events'):
                    self.display.process_events()
                    
        except KeyboardInterrupt:
            self.stop()
            print("\nAnimation sequence stopped.")