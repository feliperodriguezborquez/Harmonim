"""
Configuration settings for Harmonim.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
from .utils import get_relative_path

@dataclass
class Config:
    """Global configuration for Harmonim."""
    # Default renderer settings
    default_renderer: str = "manim"
    
    # Animation settings
    animation_speed: float = 1.0
    resolution: tuple[int, int] = (3840, 2160)
    background_color: str = "#FFFFFF"
    
    # Output settings
    output_dir: str = "output"
    
    # Debug settings
    debug: bool = False
    log_level: str = "INFO"
    
    # Font settings
    font_path: str = field(default_factory=lambda: get_relative_path("assets/fonts/Bravura.otf"))

# Global configuration instance
config = Config()

def update_config(**kwargs) -> None:
    """Update the global configuration."""
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise AttributeError(f"Invalid config option: {key}")
