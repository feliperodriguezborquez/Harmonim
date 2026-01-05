"""
Core functionality for Harmonim.

This module contains the fundamental classes and utilities used throughout the library,
including the animation system, configuration, and base classes for musical elements.
"""

from .config import config, update_config
from .animation import (
    Animatable,
    Animation,
    Transform,
    FadeIn,
    FadeOut,
    AnimationGroup,
    Succession,
    animate,
)

__all__ = [
    'config',
    'update_config',
    'Animatable',
    'Animation',
    'Transform',
    'FadeIn',
    'FadeOut',
    'AnimationGroup',
    'Succession',
    'animate',
]
