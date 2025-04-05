#!/usr/bin/env python3
"""
Game animations for Unicorn HAT Mini.

This module contains interactive game animations.
"""

import time
import math
import random
import colorsys

from animation import Animation, register_animation


# This file is intentionally left as a placeholder
# Add more game-based animations here

# @register_animation
class SnakeGameAnimation(Animation):
    """Interactive Snake game animation."""
    
    def setup(self):
        """Set up the snake game."""
        super().setup()
        
        # Mark as interactive
        self.config['interactive'] = True
        
        # Initialize snake
        self.snake = [(self.width // 2, self.height // 2)]
        self.direction = (1, 0)  # Right
        self.food = None
        self.place_food()
        
        # Game parameters
        self.move_interval = self.config.get('move_interval', 0.2)  # seconds between moves
        self.last_move_time = self.start_time
        
        # Register button handlers
        self.button_map = {
            self.display.BUTTON_A: (0, -1),  # Up
            self.display.BUTTON_B: (-1, 0),  # Left
            self.display.BUTTON_X: (0, 1),   # Down
            self.display.BUTTON_Y: (1, 0)    # Right
        }
    
    def place_food(self):
        """Place a food item at a random empty location."""
        empty_positions = []
        for x in range(self.width):
            for y in range(self.height):
                pos = (x, y)
                if pos not in self.snake:
                    empty_positions.append(pos)
        
        if empty_positions:
            self.food = random.choice(empty_positions)
    
    def update(self, dt):
        """Update the snake game."""
        self.display.clear()
        
        # Check if it's time to move the snake
        current_time = time.time()
        if current_time - self.last_move_time >= self.move_interval:
            self.last_move_time = current_time
            
            # Get the current head position
            head_x, head_y = self.snake[0]
            
            # Calculate the new head position
            dx, dy = self.direction
            new_head = ((head_x + dx) % self.width, (head_y + dy) % self.height)
            
            # Check if the snake hit itself
            if new_head in self.snake:
                # Game over - reset snake
                self.snake = [(self.width // 2, self.height // 2)]
                self.place_food()
            else:
                # Add the new head
                self.snake.insert(0, new_head)
                
                # Check if the snake ate the food
                if new_head == self.food:
                    # Grow the snake (don't remove the tail)
                    self.place_food()
                    
                    # Check win condition (snake fills the screen)
                    if len(self.snake) >= self.width * self.height:
                        # Win! Reset the snake
                        self.snake = [(self.width // 2, self.height // 2)]
                        self.place_food()
                else:
                    # Remove the tail
                    self.snake.pop()
        
        # Draw the snake
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                # Head is white
                self.display.set_pixel(x, y, 255, 255, 255)
            else:
                # Body is green with varying brightness
                brightness = 1.0 - (i / len(self.snake)) * 0.5
                g = int(255 * brightness)
                self.display.set_pixel(x, y, 0, g, 0)
        
        # Draw the food (red)
        if self.food:
            # Make food pulsate
            pulse = (math.sin(time.time() * 5) + 1) / 2
            r = 150 + int(105 * pulse)
            self.display.set_pixel(self.food[0], self.food[1], r, 0, 0)
    
    def handle_button_press(self, button):
        """Handle button presses to change snake direction."""
        if button in self.button_map:
            # Get the new direction
            new_dir = self.button_map[button]
            
            # Don't allow 180 degree turns
            dx, dy = self.direction
            new_dx, new_dy = new_dir
            
            if not (dx == -new_dx and dy == -new_dy):
                self.direction = new_dir
                return True
        
        return False
