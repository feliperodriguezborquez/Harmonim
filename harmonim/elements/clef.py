"""
Clef classes for Harmonim.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple

from .base import MusicElement
from ..core.utils import Color

class Clef(MusicElement):
    """Base class for all clefs."""
    
    def __init__(
        self,
        name: str,
        symbol: str,
        position: float,
        octave_change: int = 0,
        **kwargs
    ):
        """Initialize a Clef.
        
        Args:
            name: Name of the clef (e.g., 'treble', 'bass')
            symbol: LilyPond symbol for the clef (e.g., 'treble', 'bass')
            position: Position on the staff where the clef is placed
            octave_change: Octave transposition (0 = none, 1 = up an octave, -1 = down an octave)
        """
        super().__init__(**kwargs)
        self.name = name
        self.symbol = symbol
        self.position = position
        self.octave_change = octave_change
        
        # Duration is 0 for clefs (they don't take up time)
        self.duration = 0.0
    
    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the clef to LilyPond syntax."""
        octave = ""
        if self.octave_change > 0:
            octave = "^\"\"" + "'" * self.octave_change + ' '
        elif self.octave_change < 0:
            octave = "^\"\"" + "," * abs(self.octave_change) + ' '
        
        return f"\\clef {octave}{self.symbol}"
    
    def to_manim(self):
        """Convert the clef to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def get_pitch_position(self, pitch: str, octave: int) -> float:
        """Get the vertical position of a pitch on the staff.
        
        Args:
            pitch: The pitch name (e.g., 'C', 'D', 'E', etc.)
            octave: The octave number (4 = middle C)
            
        Returns:
            The vertical position on the staff (0 = middle line)
        """
        pitch_map = {
            'C': 0, 'D': 1, 'E': 2, 'F': 3,
            'G': 4, 'A': 5, 'B': 6
        }
        
        # Calculate position relative to middle C (C4)
        base_pitch = pitch[0].upper()
        if base_pitch not in pitch_map:
            raise ValueError(f"Invalid pitch: {pitch}")
        
        # Calculate the position relative to the clef's reference point
        # Middle C (C4) is at position 0
        position = (octave - 4) * 7 + pitch_map[base_pitch]
        
        # Adjust for the clef's position
        # The clef's position is where middle C is located
        position -= self.position
        
        return position
    
    def copy(self) -> 'Clef':
        """Create a copy of this clef."""
        return self.__class__(
            name=self.name,
            symbol=self.symbol,
            position=self.position,
            octave_change=self.octave_change,
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )

class TrebleClef(Clef):
    """Treble clef (G clef)."""
    
    def __init__(self, octave_change: int = 0, **kwargs):
        """Initialize a treble clef.
        
        Args:
            octave_change: Octave transposition (0 = none, 1 = up an octave, -1 = down an octave)
        """
        super().__init__(
            name="treble",
            symbol="treble",
            position=6,  # Middle C is one ledger line below the staff
            octave_change=octave_change,
            **kwargs
        )

class BassClef(Clef):
    """Bass clef (F clef)."""
    
    def __init__(self, octave_change: int = 0, **kwargs):
        """Initialize a bass clef.
        
        Args:
            octave_change: Octave transposition (0 = none, 1 = up an octave, -1 = down an octave)
        """
        super().__init__(
            name="bass",
            symbol="bass",
            position=-6,  # Middle C is one ledger line above the staff
            octave_change=octave_change,
            **kwargs
        )

class AltoClef(Clef):
    """Alto clef (C clef on the third line)."""
    
    def __init__(self, octave_change: int = 0, **kwargs):
        """Initialize an alto clef.
        
        Args:
            octave_change: Octave transposition (0 = none, 1 = up an octave, -1 = down an octave)
        """
        super().__init__(
            name="alto",
            symbol="alto",
            position=0,  # Middle C is on the middle line
            octave_change=octave_change,
            **kwargs
        )

class TenorClef(Clef):
    """Tenor clef (C clef on the fourth line)."""
    
    def __init__(self, octave_change: int = 0, **kwargs):
        """Initialize a tenor clef.
        
        Args:
            octave_change: Octave transposition (0 = none, 1 = up an octave, -1 = down an octave)
        """
        super().__init__(
            name="tenor",
            symbol="tenor",
            position=2,  # Middle C is on the second space from the top
            octave_change=octave_change,
            **kwargs
        )

class PercussionClef(Clef):
    """Percussion clef."""
    
    def __init__(self, **kwargs):
        """Initialize a percussion clef."""
        super().__init__(
            name="percussion",
            symbol="percussion",
            position=0,  # Not used for percussion
            **kwargs
        )
    
    def get_pitch_position(self, pitch: str, octave: int) -> float:
        """Percussion clef doesn't have pitch positions."""
        return 0.0

# Common clef instances for convenience
TREBLE = TrebleClef()
BASS = BassClef()
ALTO = AltoClef()
TENOR = TenorClef()
PERCUSSION = PercussionClef()
