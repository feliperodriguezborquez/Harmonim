"""
Utility functions for Harmonim.
"""
import os
import logging
from typing import Any, Dict, List, Optional, TypeVar, Type
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("harmonim")

T = TypeVar('T')

def ensure_dir(path: str) -> None:
    """Ensure that a directory exists, create it if it doesn't."""
    Path(path).mkdir(parents=True, exist_ok=True)

def to_snake_case(s: str) -> str:
    """Convert a string to snake_case."""
    return s.lower().replace(' ', '_')

def get_relative_path(relative_path: str) -> str:
    """Get an absolute path from a path relative to the project root."""
    return str(Path(__file__).parent.parent / relative_path)

def validate_type(value: Any, expected_type: Type[T], param_name: str) -> T:
    """Validate that a value is of the expected type."""
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Expected {param_name} to be of type {expected_type.__name__}, "
            f"got {type(value).__name__} instead"
        )
    return value

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between a minimum and maximum."""
    return max(min_val, min(value, max_val))

class Color:
    """Utility class for working with colors."""
    def __init__(self, r: float, g: float, b: float, a: float = 1.0):
        self.r = clamp(r, 0.0, 1.0)
        self.g = clamp(g, 0.0, 1.0)
        self.b = clamp(b, 0.0, 1.0)
        self.a = clamp(a, 0.0, 1.0)
    
    def to_hex(self) -> str:
        """Convert the color to a hex string."""
        return f"#{int(self.r*255):02x}{int(self.g*255):02x}{int(self.b*255):02x}"
    
    def to_rgba(self) -> tuple[float, float, float, float]:
        """Convert the color to an RGBA tuple."""
        return (self.r, self.g, self.b, self.a)
    
    @classmethod
    def from_hex(cls, hex_str: str) -> 'Color':
        """Create a Color from a hex string."""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3:
            hex_str = ''.join([c * 2 for c in hex_str])
        
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        a = int(hex_str[6:8], 16) / 255.0 if len(hex_str) > 6 else 1.0
        
        return cls(r, g, b, a)
