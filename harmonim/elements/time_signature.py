"""
Time signature classes for Harmonim.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, Union

from .base import MusicElement
from ..core.utils import Color

class TimeSignature(MusicElement):
    """Represents a time signature in musical notation."""
    
    def __init__(
        self,
        numerator: int = 4,
        denominator: int = 4,
        symbol: Optional[str] = None,
        **kwargs
    ):
        """Initialize a TimeSignature.
        
        Args:
            numerator: The top number of the time signature (beats per measure)
            denominator: The bottom number of the time signature (note value that gets the beat)
            symbol: Special symbol for common time signatures ('C' for common time, 'C|' for cut time)
        """
        super().__init__(**kwargs)
        
        if symbol is not None:
            if symbol.upper() == 'C':
                self.numerator = 4
                self.denominator = 4
                self.symbol = 'C'
            elif symbol.upper() in ('C|', '¢'):
                self.numerator = 2
                self.denominator = 2
                self.symbol = r'\time 2/2'  # LilyPond's way of representing cut time
            else:
                raise ValueError(f"Unknown time signature symbol: {symbol}")
        else:
            if not isinstance(numerator, int) or numerator < 1:
                raise ValueError("Numerator must be a positive integer")
            if denominator not in (1, 2, 4, 8, 16, 32, 64):
                raise ValueError("Denominator must be a power of 2 (1, 2, 4, 8, 16, 32, or 64)")
            
            self.numerator = numerator
            self.denominator = denominator
            self.symbol = None
        
        # Duration is 0 for time signatures (they don't take up time)
        self.duration = 0.0
    
    @property
    def beats_per_measure(self) -> float:
        """Get the number of beats per measure."""
        return self.numerator * (4.0 / self.denominator)
    
    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the time signature to LilyPond syntax."""
        if self.symbol == 'C':
            return "\\time 4/4"
        elif self.symbol == '\\time 2/2':
            return "\\time 2/2"
        else:
            return f"\\time {self.numerator}/{self.denominator}"
    
    def to_manim(self):
        """Convert the time signature to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def is_compound(self) -> bool:
        """Check if the time signature is compound (numerator is divisible by 3 and greater than 3)."""
        return self.numerator > 3 and self.numerator % 3 == 0
    
    def is_simple(self) -> bool:
        """Check if the time signature is simple (not compound)."""
        return not self.is_compound()
    
    def get_beat_unit(self) -> float:
        """Get the duration of one beat in whole notes."""
        return 4.0 / self.denominator
    
    def get_measure_duration(self) -> float:
        """Get the duration of a full measure in whole notes."""
        return self.numerator * self.get_beat_unit()
    
    def get_beat_grouping(self) -> Tuple[int, int]:
        """Get the beat grouping as a tuple (beats, base)."""
        if self.is_compound():
            # Compound meters are grouped in 3s
            return (self.numerator // 3, self.denominator * 3 // 2)
        else:
            # Simple meters are grouped as written
            return (self.numerator, self.denominator)
    
    def copy(self) -> 'TimeSignature':
        """Create a copy of this time signature."""
        if self.symbol:
            return TimeSignature(symbol=self.symbol, color=self.color, opacity=self.opacity, **self.properties)
        else:
            return TimeSignature(
                numerator=self.numerator,
                denominator=self.denominator,
                color=self.color,
                opacity=self.opacity,
                **self.properties
            )

# Common time signatures for convenience
COMMON_TIME = TimeSignature(symbol='C')
CUT_TIME = TimeSignature(symbol='C|')
FOUR_FOUR = TimeSignature(4, 4)
THREE_FOUR = TimeSignature(3, 4)
TWO_FOUR = TimeSignature(2, 4)
SIX_EIGHT = TimeSignature(6, 8)
NINE_EIGHT = TimeSignature(9, 8)
TWELVE_EIGHT = TimeSignature(12, 8)
