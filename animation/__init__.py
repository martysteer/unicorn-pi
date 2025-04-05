#!/usr/bin/env python3
"""
Animation package for Unicorn HAT Mini.

This package provides a framework for creating and sequencing animations
for the Unicorn HAT Mini.
"""

from .base import Animation
from .registry import (
    register_animation,
    get_animation_class,
    get_animation_names,
    create_animation,
    discover_animations
)
from .sequencer import (
    AnimationSequencer,
    # TransitionAnimation,
    # FadeTransition
)

# Define exports
__all__ = [
    'Animation',
    'register_animation',
    'get_animation_class',
    'get_animation_names',
    'create_animation',
    'discover_animations',
    'AnimationSequencer',
    'TransitionAnimation',
    'FadeTransition'
]