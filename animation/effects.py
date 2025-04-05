#!/usr/bin/env python3
"""
Example animations for Unicorn HAT Mini.

This module contains several example animations implemented using the Animation base class.
"""

import time
import math
import random
import colorsys

from animation import Animation, register_animation


@register_animation
class RainbowAnimation(Animation):
    """Rainbow animation that moves colors across the display."""
    
    def update(self, dt):
        """Update the rainbow animation."""
        self.display.clear()
        
        # Calculate animation time
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


@register_animation
class SpiralAnimation(Animation):
    """Spiral animation that draws spiraling patterns."""
    
    def update(self, dt):
        """Update the spiral animation."""
        self.display.clear()
        
        # Calculate animation time
        t = time.time() - self.start_time
        
        # Define spiral parameters
        max_radius = math.sqrt(self.width**2 + self.height**2) / 2
        center_x, center_y = self.width // 2, self.height // 2
        
        # Number of spiral arms
        num_arms = self.config.get('num_arms', 2)
        
        # Rotation speed
        rotation_speed = self.config.get('rotation_speed', 2.0)
        
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
                spiral_angle = (angle + t * rotation_speed) % (2 * math.pi)
                spiral_r = max_radius * spiral_angle / (2 * math.pi) * num_arms
                
                # Determine if this point is on the spiral
                if abs(radius - spiral_r % max_radius) < 1.0:
                    # Color based on angle
                    hue = (spiral_angle / (2 * math.pi) + t / 2) % 1.0
                    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                    self.display.set_pixel(x, y, r, g, b)


@register_animation
class RainAnimation(Animation):
    """Rain animation that simulates raindrops falling."""
    
    def setup(self):
        """Set up the rain animation."""
        super().setup()
        self.drops = []
        self.drop_rate = self.config.get('drop_rate', 0.3)
        self.drop_speed = self.config.get('drop_speed', 5.0)
        
    def update(self, dt):
        """Update the rain animation."""
        self.display.clear()
        
        # Possibly create a new drop
        if random.random() < self.drop_rate * dt:
            x = random.randint(0, self.width - 1)
            self.drops.append({'x': x, 'y': 0, 'speed': random.uniform(3.0, self.drop_speed)})
        
        # Update existing drops
        new_drops = []
        for drop in self.drops:
            # Move the drop down
            drop['y'] += drop['speed'] * dt
            
            # If the drop is still on screen, keep it
            if drop['y'] < self.height:
                new_drops.append(drop)
                
                # Draw the drop
                y = int(drop['y'])
                if 0 <= y < self.height:
                    # Blue color with varying intensity
                    intensity = 1.0 - (drop['y'] / self.height)
                    r, g, b = 0, int(100 * intensity), int(255 * intensity)
                    self.display.set_pixel(drop['x'], y, r, g, b)
        
        self.drops = new_drops


@register_animation
class ExplosionAnimation(Animation):
    """Explosion animation that radiates from the center."""
    
    def update(self, dt):
        """Update the explosion animation."""
        self.display.clear()
        
        # Calculate animation progress (0.0 to 1.0)
        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / self.duration)
        
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


@register_animation
class ForestFireAnimation(Animation):
    """Forest fire cellular automaton animation."""
    
    def setup(self):
        """Set up the forest fire animation."""
        super().setup()
        
        # Forest fire parameters
        self.p_tree = self.config.get('p_tree', 0.01)  # Probability of tree growth
        self.p_fire = self.config.get('p_fire', 0.0005)  # Probability of lightning
        self.initial_density = self.config.get('initial_density', 0.55)  # Initial tree density
        
        # Colors
        self.tree_color = (0, 255, 0)  # Green
        self.fire_color = (255, 0, 0)  # Red
        self.empty_color = (0, 0, 0)   # Black
        
        # Initialize grid
        self.grid = {}
        for x in range(self.width):
            for y in range(self.height):
                if random.random() <= self.initial_density:
                    self.grid[(x, y)] = self.tree_color
                else:
                    self.grid[(x, y)] = self.empty_color
    
    def update(self, dt):
        """Update the forest fire animation."""
        # Neighborhood offsets for checking neighbors
        neighborhood = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        # Create a new grid to store the updated state
        new_grid = {}
        
        # Update each cell based on the rules
        for x in range(self.width):
            for y in range(self.height):
                cell = self.grid.get((x, y), self.empty_color)
                
                if cell == self.fire_color:
                    # Fire dies out
                    new_grid[(x, y)] = self.empty_color
                    
                elif cell == self.empty_color:
                    # Empty space, may grow a tree
                    if random.random() <= self.p_tree:
                        new_grid[(x, y)] = self.tree_color
                    else:
                        new_grid[(x, y)] = self.empty_color
                        
                elif cell == self.tree_color:
                    # Tree may catch fire from neighbors or lightning
                    has_fire_neighbor = False
                    
                    # Check if any neighbors are on fire
                    for dx, dy in neighborhood:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.grid.get((nx, ny)) == self.fire_color:
                                has_fire_neighbor = True
                                break
                    
                    if has_fire_neighbor or random.random() <= self.p_fire:
                        # Tree catches fire
                        new_grid[(x, y)] = self.fire_color
                    else:
                        # Tree stays a tree
                        new_grid[(x, y)] = self.tree_color
        
        # Update the grid
        self.grid = new_grid
        
        # Draw the grid to the display
        self.display.clear()
        for (x, y), color in self.grid.items():
            self.display.set_pixel(x, y, *color)


@register_animation(name="PulsingHeartAnimation")
class PulsingHeart(Animation):
    """Displays a pulsing heart animation."""
    
    def setup(self):
        """Set up the pulsing heart animation."""
        super().setup()
        
        # Heart shape pixels (for a small display)
        self.heart_pixels = [
            (3, 1), (4, 1), (8, 1), (9, 1),
            (2, 2), (5, 2), (7, 2), (10, 2),
            (1, 3), (6, 3), (11, 3),
            (1, 4), (11, 4),
            (2, 5), (10, 5),
            (3, 6), (9, 6),
            (4, 7), (8, 7),
            (5, 8), (6, 8), (7, 8)
        ]
        
        self.pulse_rate = self.config.get('pulse_rate', 1.0)  # Pulses per second
    
    def update(self, dt):
        """Update the heart animation."""
        self.display.clear()
        
        # Calculate the pulse (0.0 to 1.0)
        t = time.time() - self.start_time
        pulse = (math.sin(t * self.pulse_rate * 2 * math.pi - math.pi/2) + 1) / 2
        
        # Color shifting from dark red to bright red
        min_brightness = 0.3
        brightness = min_brightness + (1.0 - min_brightness) * pulse
        
        # Calculate RGB color for heart
        r = int(255 * brightness)
        g = int(50 * brightness)
        b = int(50 * brightness)
        
        # Draw the heart
        for x, y in self.heart_pixels:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.display.set_pixel(x, y, r, g, b)


@register_animation
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


@register_animation
class DemoSequenceAnimation(Animation):
    """Demo sequence that cycles through multiple animation effects."""
    
    def setup(self):
        """Set up the demo sequence."""
        super().setup()
        
        # Animation effects to cycle through
        self.effects = [
            self.tunnel_effect,
            self.rainbow_search_effect, 
            self.checker_effect,
            self.swirl_effect
        ]
        
        # Generate a lookup table for 8-bit hue to RGB conversion
        self.hue_to_rgb = []
        for i in range(0, 360):
            self.hue_to_rgb.append(colorsys.hsv_to_rgb(i / 359.0, 1, 1))
        
        # Time for each effect
        self.effect_duration = self.config.get('effect_duration', 5.0)
    
    def update(self, dt):
        """Update the demo sequence."""
        self.display.clear()
        
        # Calculate time and progress
        t = time.time() - self.start_time
        f = t / self.effect_duration
        fx = int(f) % len(self.effects)
        next_fx = (fx + 1) % len(self.effects)
        
        # Calculate step for animation
        step = (t * 50)
        
        # Update display using current effect and possibly blend with next effect
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = self.effects[fx](x, y, step)
                
                # Blend with next effect if we're in the transition period
                if f % 1.0 > 0.75:
                    r2, g2, b2 = self.effects[next_fx](x, y, step)
                    ratio = (1.0 - (f % 1.0)) / 0.25
                    r = r * ratio + r2 * (1.0 - ratio)
                    g = g * ratio + g2 * (1.0 - ratio)
                    b = b * ratio + b2 * (1.0 - ratio)
                
                # Clamp RGB values
                r = int(max(0, min(255, r)))
                g = int(max(0, min(255, g)))
                b = int(max(0, min(255, b)))
                
                self.display.set_pixel(x, y, r, g, b)
    
    def tunnel_effect(self, x, y, step):
        """Zoom tunnel effect."""
        speed = step / 100.0
        x -= (self.width / 2)
        y -= (self.height / 2)
        xo = math.sin(step / 27.0) * 2
        yo = math.cos(step / 18.0) * 2
        x += xo
        y += yo
        
        if y == 0:
            if x < 0:
                angle = -(math.pi / 2)
            else:
                angle = (math.pi / 2)
        else:
            angle = math.atan(x / y)
            
        if y > 0:
            angle += math.pi
            
        angle /= 2 * math.pi  # convert angle to 0...1 range
        hyp = math.sqrt(x*x + y*y)
        shade = hyp / 2.1
        shade = 1 if shade > 1 else shade
        angle += speed
        depth = speed + (hyp / 10)
        
        col1 = self.hue_to_rgb[int(step) % 359]
        col1 = (col1[0] * 0.8, col1[1] * 0.8, col1[2] * 0.8)
        col2 = self.hue_to_rgb[int(step) % 359]
        col2 = (col2[0] * 0.3, col2[1] * 0.3, col2[2] * 0.3)
        col = col1 if int(abs(angle * 6.0)) % 2 == 0 else col2
        td = .3 if int(abs(depth * 3.0)) % 2 == 0 else 0
        col = (col[0] + td, col[1] + td, col[2] + td)
        col = (col[0] * shade, col[1] * shade, col[2] * shade)
        
        return (col[0] * 255, col[1] * 255, col[2] * 255)
    
    def rainbow_search_effect(self, x, y, step):
        """Rainbow search spotlight effect."""
        xs = math.sin(step / 100.0) * 20.0
        ys = math.cos(step / 100.0) * 20.0
        scale = ((math.sin(step / 60.0) + 1.0) / 5.0) + 0.2
        r = math.sin((x + xs) * scale) + math.cos((y + xs) * scale)
        g = math.sin((x + xs) * scale) + math.cos((y + ys) * scale)
        b = math.sin((x + ys) * scale) + math.cos((y + ys) * scale)
        
        return (r * 255, g * 255, b * 255)
    
    def checker_effect(self, x, y, step):
        """Roto-zooming checker board effect."""
        x -= (self.width / 2)
        y -= (self.height / 2)
        angle = step / 10.0
        s = math.sin(angle)
        c = math.cos(angle)
        xs = x * c - y * s
        ys = x * s + y * c
        xs -= math.sin(step / 200.0) * 40.0
        ys -= math.cos(step / 200.0) * 40.0
        scale = (math.sin(step / 50.0) / 8.0) + 0.25
        xs *= scale
        ys *= scale
        xo = abs(xs) - int(abs(xs))
        yo = abs(ys) - int(abs(ys))
        v = 0 if (math.floor(xs) + math.floor(ys)) % 2 else 1 if xo > .1 and yo > .1 else .5
        r, g, b = self.hue_to_rgb[int(step) % 359]
        
        return (r * v * 255, g * v * 255, b * v * 255)
    
    def swirl_effect(self, x, y, step):
        """Twisty swirly goodness effect."""
        x -= (self.width / 2)
        y -= (self.height / 2)
        dist = math.sqrt(x*x + y*y) / 2.0
        angle = (step / 10.0) + (dist * 1.5)
        s = math.sin(angle)
        c = math.cos(angle)
        xs = x * c - y * s
        ys = x * s + y * c
        r = abs(xs + ys)
        r = r * 12.0
        r -= 20
        
        return (r, r + (s * 130), r + (c * 130))