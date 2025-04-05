#!/usr/bin/env python3
"""
Animation registry for Unicorn HAT Mini animations.

This module provides functions for registering, discovering, and loading animations.
"""

import importlib
import pkgutil
import inspect
import os
import sys

# Dictionary to store all registered animations
_ANIMATIONS = {}


def register_animation(cls=None, name=None):
    """Register an animation class.
    
    This function can be used as a decorator or called directly.
    
    Args:
        cls: The animation class to register
        name: Optional name to register the animation under
            If not provided, the class name will be used
    
    Returns:
        The registered class (for decorator usage)
    """
    def _register(cls):
        animation_name = name or cls.__name__
        _ANIMATIONS[animation_name] = cls
        return cls
        
    if cls is None:
        # Called as @register_animation(name="example")
        return _register
    else:
        # Called as @register_animation
        return _register(cls)


def get_animation_class(name):
    """Get an animation class by name.
    
    Args:
        name: The name of the animation
        
    Returns:
        The animation class, or None if not found
    """
    return _ANIMATIONS.get(name)


def get_animation_names():
    """Get a list of all registered animation names.
    
    Returns:
        List of animation names
    """
    return sorted(_ANIMATIONS.keys())


def create_animation(name, display, config=None):
    """Create an instance of an animation by name.
    
    Args:
        name: The name of the animation
        display: The UnicornHATMini display object
        config: Optional configuration dictionary
        
    Returns:
        An instance of the animation, or None if not found
    """
    cls = get_animation_class(name)
    if cls is None:
        return None
        
    return cls(display, config)


def discover_animations(package):
    """Discover and register all animations in a package.
    
    This function recursively imports all modules in a package
    and registers any Animation subclasses it finds.
    
    Args:
        package: The package to scan for animations
    """
    # Import the package
    pkg_module = importlib.import_module(package)
    
    # Get the package directory
    pkg_path = os.path.dirname(pkg_module.__file__)
    
    # Recursively import all modules in the package
    for _, name, is_pkg in pkgutil.iter_modules([pkg_path]):
        module_name = f"{package}.{name}"
        
        if is_pkg:
            # Recurse into subpackages
            discover_animations(module_name)
        else:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Find and register all Animation subclasses in the module
            from .base import Animation
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Animation) and 
                    obj != Animation):
                    register_animation(obj)