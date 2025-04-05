#!/usr/bin/env python3
"""
Animation Sequencer with Enhanced Debugging for Unicorn HAT Mini.

This file provides an enhanced version of the AnimationSequencer class
with improved debugging output. To use this, replace or modify your
existing animation/sequencer.py with this content.
"""

import time
import json
import random


class AnimationSequencer:
    """Manages a sequence of animations with transitions and enhanced debugging."""
    
    def __init__(self, display, config_file=None, debug_level=1):
        """Initialize the animation sequencer.
        
        Args:
            display: The UnicornHATMini display
            config_file: Optional path to a configuration file
            debug_level: Debug verbosity level (0=none, 1=basic, 2=verbose)
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
        self.debug_level = debug_level
        self.sequence_start_time = None
        self.frame_count = 0
        
        # Debug initialization
        if self.debug_level >= 1:
            print(f"\n[SEQUENCER] Initializing animation sequencer")
            print(f"[SEQUENCER] Debug level: {self.debug_level}")
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Configuration loaded")
            if self.debug_level >= 2:
                print(f"[SEQUENCER] Config: {self.config}")
        
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
            'default_duration': 5.0,
            'debug_level': self.debug_level
        }
        
        if config_file:
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Loading config from: {config_file}")
                
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                
                if self.debug_level >= 1:
                    print(f"[SEQUENCER] Config loaded successfully")
            except (IOError, json.JSONDecodeError) as e:
                print(f"[SEQUENCER] Error loading config file: {e}")
        else:
            if self.debug_level >= 1:
                print(f"[SEQUENCER] No config file specified, using defaults")
        
        return default_config
    
    def _init_animations(self):
        """Initialize animations from config."""
        from .registry import get_animation_names, create_animation
        
        animation_configs = self.config.get('animations', [])
        
        if not animation_configs:
            # If no animations in config, use all available animations
            if self.debug_level >= 1:
                print(f"[SEQUENCER] No animations specified in config, using all available")
                
            for name in get_animation_names():
                animation_configs.append({
                    'name': name,
                    'duration': self.config.get('default_duration', 5.0),
                    'debug_level': self.debug_level
                })
        
        # Create animation objects
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Creating {len(animation_configs)} animations:")
            
        for anim_config in animation_configs:
            name = anim_config.get('name')
            if name:
                # Ensure debug level is passed to animation
                if 'debug_level' not in anim_config:
                    anim_config['debug_level'] = self.debug_level
                    
                anim = create_animation(name, self.display, anim_config)
                if anim:
                    self.animations.append(anim)
                    if self.debug_level >= 1:
                        print(f"[SEQUENCER]   - {name} (duration: {anim_config.get('duration', self.config.get('default_duration'))}s)")
                else:
                    print(f"[SEQUENCER] Warning: Failed to create animation '{name}'")
        
        if self.config.get('shuffle', False):
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Shuffling animations")
            random.shuffle(self.animations)
        
        # Initialize the first animation
        if self.animations:
            self.current_animation = self.animations[0]
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Initial animation: {self.current_animation.name}")
            self.current_animation.setup()
        else:
            print(f"[SEQUENCER] Warning: No animations available to play!")
    
    def _create_transition(self, from_anim, to_anim):
        """Create a transition animation between two animations.
        
        Args:
            from_anim: The animation to transition from
            to_anim: The animation to transition to
            
        Returns:
            A transition animation
        """
        from .registry import create_animation
        
        transition_type = self.config.get('transition', 'fade')
        transition_duration = self.config.get('transition_duration', 1.0)
        
        if self.debug_level >= 1:
            from_name = from_anim.name if from_anim else "None"
            to_name = to_anim.name if to_anim else "None"
            print(f"[SEQUENCER] Creating {transition_type} transition: {from_name} → {to_name} ({transition_duration}s)")
        
        transition_config = {
            'from_anim': from_anim,
            'to_anim': to_anim,
            'duration': transition_duration,
            'debug_level': self.debug_level
        }
        
        # Use the animation registry to create the transition
        if transition_type == 'fade':
            from .sequencer import FadeTransition
            return FadeTransition(self.display, transition_config)
        else:
            print(f"[SEQUENCER] Warning: Unsupported transition type '{transition_type}', falling back to fade")
            from .sequencer import FadeTransition
            return FadeTransition(self.display, transition_config)
    
    def next(self):
        """Advance to the next animation."""
        if not self.animations:
            if self.debug_level >= 1:
                print(f"[SEQUENCER] No animations available, cannot advance")
            return
            
        # If we're already transitioning, do nothing
        if self.is_transitioning:
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Already transitioning, ignoring next() call")
            return
            
        # Determine the next animation
        next_index = (self.current_index + 1) % len(self.animations)
        
        # If we've reached the end and not looping, stop
        if next_index == 0 and not self.config.get('loop', True):
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Reached end of sequence and loop=False, stopping")
            self.current_animation.cleanup()
            self.current_animation = None
            self.is_running = False
            return
            
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Advancing to next animation: {self.current_index} → {next_index}")
            
        self.current_index = next_index
        self.next_animation = self.animations[next_index]
        self.next_animation.setup()
        
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Next animation: {self.next_animation.name}")
        
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
            if self.debug_level >= 1:
                print(f"[SEQUENCER] No animations available, cannot go back")
            return
            
        # If we're already transitioning, do nothing
        if self.is_transitioning:
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Already transitioning, ignoring previous() call")
            return
            
        # Determine the previous animation
        prev_index = (self.current_index - 1) % len(self.animations)
        
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Going to previous animation: {self.current_index} → {prev_index}")
            
        self.current_index = prev_index
        self.next_animation = self.animations[prev_index]
        self.next_animation.setup()
        
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Previous animation: {self.next_animation.name}")
        
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
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Invalid animation index: {index}")
            return
            
        # If we're already transitioning, do nothing
        if self.is_transitioning:
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Already transitioning, ignoring jump_to({index}) call")
            return
            
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Jumping to animation index {index}")
            
        self.current_index = index
        self.next_animation = self.animations[index]
        self.next_animation.setup()
        
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Target animation: {self.next_animation.name}")
        
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
        if self.debug_level >= 2:
            print(f"[SEQUENCER] Button press: {button}")
            
        # First, check if the current animation handles this button
        if self.current_animation and self.current_animation.handle_button_press(button):
            if self.debug_level >= 2:
                print(f"[SEQUENCER] Button {button} handled by animation: {self.current_animation.name}")
            return True
            
        # Then check if we have a handler for this button
        handler = self.button_handlers.get(button)
        if handler:
            if self.debug_level >= 2:
                print(f"[SEQUENCER] Button {button} handled by registered handler")
            handler()
            return True
            
        if self.debug_level >= 2:
            print(f"[SEQUENCER] Button {button} not handled")
            
        return False
    
    def register_button_handler(self, button, handler):
        """Register a handler for a button press.
        
        Args:
            button: The button to handle
            handler: Function to call when the button is pressed
        """
        self.button_handlers[button] = handler
        if self.debug_level >= 2:
            print(f"[SEQUENCER] Registered handler for button {button}")
    
    def start(self):
        """Start the animation sequence."""
        if not self.animations:
            print(f"[SEQUENCER] No animations to start!")
            return
            
        self.is_running = True
        self.is_paused = False
        self.sequence_start_time = time.time()
        self.frame_count = 0
        
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Starting animation sequence")
            if self.debug_level >= 2:
                print(f"[SEQUENCER] Start time: {time.strftime('%H:%M:%S')}")
        
        if not self.current_animation:
            self.current_animation = self.animations[0]
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Initial animation: {self.current_animation.name}")
            self.current_animation.setup()
    
    def stop(self):
        """Stop the animation sequence."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.debug_level >= 1:
            elapsed = time.time() - self.sequence_start_time if self.sequence_start_time else 0
            print(f"[SEQUENCER] Stopping animation sequence after {elapsed:.2f}s, {self.frame_count} frames")
        
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
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Paused animation sequence")
    
    def resume(self):
        """Resume the animation sequence."""
        self.is_paused = False
        if self.debug_level >= 1:
            print(f"[SEQUENCER] Resumed animation sequence")
    
    def update(self):
        """Update the current animation or transition.
        
        Returns:
            bool: True if the animation sequence is still running
        """
        if not self.is_running:
            return self.is_running
            
        if self.is_paused:
            # Blink the first pixel slowly to indicate paused state
            if int(time.time() * 2) % 2 == 0:
                self.display.set_pixel(0, 0, 255, 0, 0)
            else:
                self.display.set_pixel(0, 0, 0, 0, 0)
            self.display.show()
            return self.is_running
            
        # Increment frame counter
        self.frame_count += 1
        
        # Periodically print sequence status
        if self.debug_level >= 1 and self.frame_count % 100 == 0:
            elapsed = time.time() - self.sequence_start_time if self.sequence_start_time else 0
            current_name = self.current_animation.name if self.current_animation else "None"
            fps = self.frame_count / elapsed if elapsed > 0 else 0
            
            print(f"[SEQUENCER] Status: current={current_name}, frame={self.frame_count}, fps={fps:.1f}")
            
        if self.is_transitioning:
            # Update the transition
            if self.transition.run_frame():
                # Transition still in progress
                return True
                
            # Transition finished, switch to next animation
            if self.debug_level >= 1:
                from_name = self.current_animation.name if self.current_animation else "None"
                to_name = self.next_animation.name if self.next_animation else "None"
                print(f"[SEQUENCER] Transition complete: {from_name} → {to_name}")
                
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
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Animation finished: {self.current_animation.name}, advancing to next")
                
            self.next()
            return True
            
        return False
    
    def run(self):
        """Run the animation sequence until stopped."""
        self.start()
        
        try:
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Entering main loop")
                
            while self.update():
                # Process display events if available
                if hasattr(self.display, 'process_events'):
                    self.display.process_events()
                    
        except KeyboardInterrupt:
            if self.debug_level >= 1:
                print(f"[SEQUENCER] Keyboard interrupt received")
            self.stop()
            print("\nAnimation sequence stopped.")