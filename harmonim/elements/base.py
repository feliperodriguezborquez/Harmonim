"""
Base classes for musical elements.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import math

from harmonim.core import Animatable
from harmonim.core.animation import Animation
from harmonim.core.utils import Color

class MusicElement(Animatable, ABC):
    """Base class for all musical elements."""
    
    def __init__(
        self,
        duration: float = 1.0,
        color: Union[str, Color, None] = None,
        opacity: float = 1.0,
        visible: bool = True,
        offset: float = 0.0,
        **kwargs
    ):
        """Initialize a musical element.
        
        Args:
            duration: Duration of the element in beats.
            color: Color of the element (can be a Color object or CSS color string).
            opacity: Opacity of the element (0.0 to 1.0).
            visible: Whether the element is visible.
            offset: Absolute offset (start time) of the element in beats.
        """
        self.duration = max(0.0, float(duration))
        self.opacity = max(0.0, min(1.0, float(opacity)))
        self.visible = bool(visible)
        self.offset = float(offset)
        self._color = None
        self.color = color  # Use property setter
        self.id = kwargs.get('id', None)
        
        # Store additional properties
        self.properties = kwargs
    
    @property
    def color(self) -> Optional[Color]:
        """Get the color of the element."""
        return self._color
    
    @color.setter
    def color(self, value: Union[str, Color, None]) -> None:
        """Set the color of the element."""
        if value is None:
            self._color = None
        elif isinstance(value, str):
            self._color = Color.from_hex(value)
        elif isinstance(value, Color):
            self._color = value
        else:
            raise TypeError(f"Color must be a string or Color object, got {type(value).__name__}")
    
    def set_opacity(self, opacity: float) -> None:
        """Set the opacity of the element."""
        self.opacity = max(0.0, min(1.0, float(opacity)))
    
    def show(self) -> None:
        """Make the element visible."""
        self.visible = True
    
    def hide(self) -> None:
        """Hide the element."""
        self.visible = False
    
    @abstractmethod
    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the element to LilyPond syntax.
        
        Args:
            svg_id: Optional ID to assign to the SVG element (for animation mapping).
            
        Returns:
            A string representing the element in LilyPond syntax.
        """
        pass
    
    @abstractmethod
    def to_manim(self):
        """Convert the element to a Manim object.
        
        Returns:
            A Manim object representing the element.
        """
        pass
    
    def interpolate(self, other: 'MusicElement', alpha: float) -> 'MusicElement':
        """Interpolate between this element and another element.
        
        Args:
            other: The other element to interpolate to.
            alpha: Interpolation factor (0.0 = self, 1.0 = other)
            
        Returns:
            A new element representing the interpolated state.
        """
        if not isinstance(other, self.__class__):
            raise TypeError(f"Cannot interpolate between {self.__class__.__name__} and {other.__class__.__name__}")
        
        # Create a copy of this element
        result = self.copy()
        
        # Interpolate properties
        result.opacity = self.opacity * (1 - alpha) + other.opacity * alpha
        
        # Interpolate color if both have colors
        if self.color is not None and other.color is not None:
            r = self.color.r * (1 - alpha) + other.color.r * alpha
            g = self.color.g * (1 - alpha) + other.color.g * alpha
            b = self.color.b * (1 - alpha) + other.color.b * alpha
            a = self.color.a * (1 - alpha) + other.color.a * alpha
            result.color = Color(r, g, b, a)
        
        # Interpolate duration
        result.duration = self.duration * (1 - alpha) + other.duration * alpha
        
        return result
    
    def copy(self) -> 'MusicElement':
        """Create a copy of this element."""
        return self.__class__(**self.__dict__)
    
    def __add__(self, other: 'MusicElement') -> 'MusicSequence':
        """Concatenate this element with another element or sequence."""
        from .sequence import MusicSequence
        return MusicSequence([self]) + other
    
    def __mul__(self, n: int) -> 'MusicSequence':
        """Repeat this element n times."""
        from .sequence import MusicSequence
        return MusicSequence([self] * n)

class PositionedElement(MusicElement):
    """Base class for elements with a position on the staff."""
    
    def __init__(
        self,
        position: float = 0.0,
        octave: int = 4,
        accidental: Optional[str] = None,
        **kwargs
    ):
        """Initialize a positioned element.
        
        Args:
            position: Position on the staff (0 = middle C, 1 = D above middle C, etc.)
            octave: Octave number (4 = middle C, 5 = one octave above, etc.)
            accidental: Accidental (None, 'sharp', 'flat', 'natural', 'double-sharp', 'double-flat')
        """
        super().__init__(**kwargs)
        self.position = float(position)
        self.octave = int(octave)
        self.accidental = accidental
    
    def get_pitch_name(self) -> str:
        """Get the pitch name (e.g., 'C', 'D', 'E', etc.)."""
        positions = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        idx = int(round(self.position)) % 7
        return positions[idx]
    
    def get_octave(self) -> int:
        """Get the octave number."""
        return self.octave + int(self.position // 7)
    
    def to_scientific_pitch(self) -> str:
        """Convert to scientific pitch notation (e.g., 'C4', 'A#3')."""
        pitch = self.get_pitch_name()
        octave = self.get_octave()
        
        if self.accidental == 'sharp':
            pitch += '#'
        elif self.accidental == 'flat':
            pitch += 'b'
        elif self.accidental == 'double-sharp':
            pitch += '##'
        elif self.accidental == 'double-flat':
            pitch += 'bb'
        
        return f"{pitch}{octave}"
    
    def to_lilypond_pitch(self) -> str:
        """Convert the pitch to LilyPond syntax."""
        pitch_map = {
            'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f',
            'G': 'g', 'A': 'a', 'B': 'b'
        }
        
        accidental_map = {
            'sharp': 'is',
            'flat': 'es',
            'natural': '',
            'double-sharp': 'isis',
            'double-flat': 'eses',
            None: ''
        }
        
        # Get base pitch and octave
        base_pitch = self.get_pitch_name()
        octave_offset = self.get_octave() - 4  # Middle C is c'
        
        # Build the pitch string
        pitch = pitch_map[base_pitch]
        accidental = accidental_map.get(self.accidental, '')
        
        # Add octave marks
        if octave_offset > 0:
            pitch += "'" * octave_offset
        elif octave_offset < 0:
            pitch += "," * abs(octave_offset)
        
        return f"{pitch}{accidental}"
    
    def interpolate(self, other: 'PositionedElement', alpha: float) -> 'PositionedElement':
        """Interpolate between this element and another positioned element."""
        if not isinstance(other, PositionedElement):
            return super().interpolate(other, alpha)
        
        result = super().interpolate(other, alpha)
        result.position = self.position * (1 - alpha) + other.position * alpha
        result.octave = int(round(self.octave * (1 - alpha) + other.octave * alpha))
        
        # Keep the accidental from the start or end based on alpha
        if alpha < 0.5:
            result.accidental = self.accidental
        else:
            result.accidental = other.accidental
        
        return result
