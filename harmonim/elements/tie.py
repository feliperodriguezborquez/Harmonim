"""
Tie class for Harmonim.
"""
from __future__ import annotations
from typing import Optional
from .base import MusicElement
from .note import Note

class Tie(MusicElement):
    """Represents a tie connecting two notes of the same pitch."""
    
    def __init__(
        self,
        start_note: Note,
        end_note: Note,
        direction: str = 'auto', # 'up', 'down', 'auto'
        **kwargs
    ):
        """Initialize a Tie.
        
        Args:
            start_note: The note where the tie starts.
            end_note: The note where the tie ends.
            direction: Direction of the tie curve.
        """
        super().__init__(**kwargs)
        self.start_note = start_note
        self.end_note = end_note
        self.direction = direction
        self.duration = 0 # Ties don't add duration themselves

    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the tie to LilyPond syntax."""
        # In LilyPond, ties are indicated by '~' after the note.
        # This is handled at the Note level usually, or by appending '~' to the start note string.
        # But since we have a separate Tie object, we might need to handle it in the Staff rendering loop
        # or modify the notes.
        # For now, return empty string as it's context dependent.
        return ""

    def to_manim(self):
        """Convert the tie to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def copy(self) -> 'Tie':
        """Create a copy of this tie."""
        return Tie(
            start_note=self.start_note, # Should we copy notes? Ideally yes if they are owned by the tie, but they are usually in the staff.
            end_note=self.end_note,
            direction=self.direction,
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )
