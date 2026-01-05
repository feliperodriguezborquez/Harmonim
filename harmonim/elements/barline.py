"""
Barline classes for Harmonim.
"""
from __future__ import annotations
from enum import Enum, auto
from typing import Optional, Dict, Any

from .base import MusicElement
from ..core.utils import Color

class BarlineType(Enum):
    """Types of barlines in musical notation."""
    SINGLE = auto()
    DOUBLE = auto()
    FINAL = auto()
    REPEAT_START = auto()
    REPEAT_END = auto()
    REPEAT_BOTH = auto()
    DASHED = auto()
    TICK = auto()
    SHORT = auto()
    NONE = auto()

class Barline(MusicElement):
    """Represents a barline in musical notation."""
    
    def __init__(
        self,
        barline_type: BarlineType = BarlineType.SINGLE,
        repeat_count: Optional[int] = None,
        **kwargs
    ):
        """Initialize a Barline.
        
        Args:
            barline_type: Type of the barline (single, double, repeat, etc.)
            repeat_count: For repeat barlines, the number of repeats
        """
        super().__init__(**kwargs)
        self.barline_type = barline_type
        self.repeat_count = repeat_count
        
        # Duration is 0 for barlines (they don't take up time)
        self.duration = 0.0
    
    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the barline to LilyPond syntax."""
        bar_map = {
            BarlineType.SINGLE: "|",
            BarlineType.DOUBLE: "||",
            BarlineType.FINAL: "|.",
            BarlineType.REPEAT_START: ":|.",
            BarlineType.REPEAT_END: ".|:",
            BarlineType.REPEAT_BOTH: ":|.:|:",
            BarlineType.DASHED: "!"
        }
        
        bar_str = bar_map.get(self.barline_type, "|")
        
        # Add repeat count if specified
        if self.repeat_count is not None and self.barline_type in (
            BarlineType.REPEAT_END,
            BarlineType.REPEAT_START,
            BarlineType.REPEAT_BOTH
        ):
            bar_str = f"{bar_str}^{self.repeat_count}"
        
        return f"\\bar \"{bar_str}\""
    
    def to_manim(self):
        """Convert the barline to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def copy(self) -> 'Barline':
        """Create a copy of this barline."""
        return Barline(
            barline_type=self.barline_type,
            repeat_count=self.repeat_count,
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )

# Common barline instances for convenience
SINGLE_BAR = Barline(BarlineType.SINGLE)
DOUBLE_BAR = Barline(BarlineType.DOUBLE)
FINAL_BAR = Barline(BarlineType.FINAL)
REPEAT_START = Barline(BarlineType.REPEAT_START)
REPEAT_END = Barline(BarlineType.REPEAT_END)
REPEAT_BOTH = Barline(BarlineType.REPEAT_BOTH)
DASHED_BAR = Barline(BarlineType.DASHED)
