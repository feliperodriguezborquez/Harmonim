"""
Beam class for Harmonim.
"""
from __future__ import annotations
from typing import List, Optional, Union
from .base import MusicElement
from .note import Note

class Beam(MusicElement):
    """Represents a beam connecting multiple notes."""
    
    def __init__(
        self,
        notes: List[Note],
        **kwargs
    ):
        """Initialize a Beam.
        
        Args:
            notes: List of notes to be beamed together.
        """
        super().__init__(**kwargs)
        self.notes = notes
        self._update_duration()
        
    def _update_duration(self) -> None:
        """Update the total duration of the beam based on its notes."""
        self.duration = sum(note.duration for note in self.notes)

    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the beam to LilyPond syntax."""
        if not self.notes:
            return ""
            
        # LilyPond uses [ and ] for beams
        # We need to attach [ to the first note and ] to the last note
        
        result = []
        for i, note in enumerate(self.notes):
            # We don't have IDs for internal notes here easily unless passed in.
            # For now, just call to_lilypond without ID for internal notes.
            note_str = note.to_lilypond()
            if i == 0:
                # Insert [ after the note (and duration) but before other things?
                # Note.to_lilypond returns "pitch duration articulations"
                # We usually append [ to the end
                note_str += "["
            elif i == len(self.notes) - 1:
                note_str += "]"
            
            result.append(note_str)
            
        return " ".join(result)

    def to_manim(self):
        """Convert the beam to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def copy(self) -> 'Beam':
        """Create a copy of this beam."""
        return Beam(
            notes=[note.copy() for note in self.notes],
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )
