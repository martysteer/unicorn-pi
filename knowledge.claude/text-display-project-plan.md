# Text Display Project Plan for Unicorn HAT Mini Animation Framework

This document outlines a 5-stage approach to enhancing the text display capabilities of the Unicorn HAT Mini animation framework.

## Stage 1: Base Text Animation Class

**Goal**: Create a foundational text animation class that extends the base `Animation` class in the framework.

**Implementation Steps**:
1. Create a new file `animation/text.py` that extends the base `Animation` class
2. Implement font loading and text rendering using PIL
3. Add default configuration options for:
   - Font selection is hardcoded custom pixel font size/basic ASCII font.
   - Text content (static string, file, etc.)
   - Text vertical positioning is in the middle of the display
   - Default colors
4. Include method to measure text dimensions
5. Implement basic static text rendering to the display
6. Add registration to the animation registry

**Example Usage**:
```python
text_animation = create_animation("TextAnimation", display, {
    "text": "Hello World",
    "position": "center"  # or (x, y) coordinates of top right origin
})
```

## Stage 2: Text Effects Development

**Goal**: Build various text effects that extend the base text animation class.

**Implementation Steps**:
1. Create the following text animation effects:
   - `StaticTextAnimation`: Simple static text display
   - `ScrollingTextAnimation`: Horizontal scrolling text (marquee)
   - `TypewriterAnimation`: Character-by-character typing effect
   - `FadeTextAnimation`: Text that fades in/out
   - `PulsingTextAnimation`: Text that pulses with size or opacity changes
2. For each effect, implement:
   - Specific configuration parameters
   - Animation timing controls
   - Update method for the animation effect
   - Registration with the animation registry

**Example Usage**:
```python
scrolling_text = create_animation("ScrollingTextAnimation", display, {
    "text": "This text will scroll across the display",
    "speed": 0.2,  # pixels per frame
    "loop": True,
    "gap": 16,  # gap between repetitions
    "direction": "left-to-right"  # or "right-to-left"
})
```

## Stage 3: Input Sources Integration

**Goal**: Develop adapters for different text input sources.

**Implementation Steps**:
1. Create a `TextSource` abstract class with common interface
2. Implement various source adapters:
   - `StaticTextSource`: Fixed text string
   - `FileTextSource`: Read from text file (with optional watch for changes)
   - `StdinTextSource`: Read from stdin (piped input)
   - `NetworkTextSource`: Fetch text from network/API
   - `CommandOutputSource`: Capture output from command execution
3. Add support for input formatting and preprocessing
4. Implement real-time updates for dynamic sources
5. Add configuration options for refresh rates, timeouts, etc.

**Example Usage**:
```python
# Using a file source that updates when the file changes
file_text = create_animation("ScrollingTextAnimation", display, {
    "text_source": {
        "type": "file",
        "path": "/var/log/system.log",
        "watch": True,
        "max_lines": 10
    },
    "speed": 0.2
})

# Using command output as source
cmd_text = create_animation("ScrollingTextAnimation", display, {
    "text_source": {
        "type": "command",
        "command": "date '+%H:%M:%S'",
        "refresh_interval": 1.0  # seconds
    }
})
```

## Stage 4: User Interactivity

**Goal**: Add button controls to modify text display parameters in real-time.

**Implementation Steps**:
1. Extend `handle_button_press` method in text animations
2. Implement common button controls:
   - Speed control (faster/slower)
   - Pause/resume scrolling
   - Change color modes/effects
   - Font size or position adjustment
   - Toggle between multiple text sources
3. Add visual feedback for button presses
4. Implement long-press and button combinations
5. Create a simple on-screen menu system for configuration changes

**Example Interaction**:
- **Button A**: Increase speed / Next item
- **Button B**: Decrease speed / Previous item
- **Button X**: Toggle color effects
- **Button Y**: Pause/Resume
- **A+X together**: Toggle text sources
- **B+Y together**: Show configuration menu

**Implementation Example**:
```python
def handle_button_press(self, button):
    """Handle button press events."""
    if button == self.display.BUTTON_A:
        self.increase_speed()
        return True
    elif button == self.display.BUTTON_B:
        self.decrease_speed()
        return True
    elif button == self.display.BUTTON_X:
        self.toggle_color_effect()
        return True
    elif button == self.display.BUTTON_Y:
        self.toggle_pause()
        return True
    return False
```

## Stage 5: Animation Sequence Integration

**Goal**: Enable text animations to be part of animation sequences in the existing framework.

**Implementation Steps**:
1. Ensure all text animations work properly with the `AnimationSequencer`
2. Add transition effects specific to text:
   - Character shuffle transition
   - Word-by-word fade
   - Letter scramble effect
3. Create compound animations that combine text with other effects
4. Add configuration in `animations.json` for text animations
5. Implement proper cleanup and state management for sequenced animations
6. Create example scripts demonstrating text in animation sequences

**Example Configuration**:
```json
{
  "animations": [
    {
      "name": "RainbowAnimation",
      "duration": 5.0
    },
    {
      "name": "ScrollingTextAnimation",
      "duration": 10.0,
      "text": "This appears after the rainbow",
      "speed": 0.2,
      "color_mode": "rainbow"
    },
    {
      "name": "ExplosionAnimation",
      "duration": 3.0
    }
  ],
  "transition": "fade",
  "transition_duration": 1.0
}
```

## Final Deliverables

After completing all five stages, the project will produce:

1. A complete set of text animation classes in the animation framework
2. Various text effects with different visual presentations
3. Flexible input sources for dynamic text content
4. Interactive button controls for user customization
5. Full integration with the animation sequencer

These enhancements will enable users to create sophisticated text displays on the Unicorn HAT Mini, from simple scrolling messages to complex interactive information displays that can show data from various sources with visually appealing effects.
