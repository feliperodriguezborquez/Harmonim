"""
Sequence classes for Harmonim.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Iterator, overload

from .base import MusicElement, PositionedElement
from ..core.utils import Color

class MusicSequence(MusicElement):
    """A sequence of music elements that can be played in order."""
    
    def __init__(
        self,
        elements: Optional[List[MusicElement]] = None,
        **kwargs
    ):
        """Initialize a MusicSequence.
        
        Args:
            elements: Initial list of music elements in this sequence
        """
        super().__init__(**kwargs)
        self.elements = elements if elements is not None else []
        self._update_duration()
    
    def _update_duration(self) -> None:
        """Update the total duration of the sequence."""
        self.duration = sum(element.duration for element in self.elements)
    
    def append(self, element: MusicElement) -> 'MusicSequence':
        """Append a music element to the sequence.
        
        Args:
            element: The music element to append
            
        Returns:
            self for method chaining
        """
        self.elements.append(element)
        self._update_duration()
        return self
    
    def extend(self, elements: List[MusicElement]) -> 'MusicSequence':
        """Extend the sequence with multiple music elements.
        
        Args:
            elements: List of music elements to add
            
        Returns:
            self for method chaining
        """
        self.elements.extend(elements)
        self._update_duration()
        return self
    
    def insert(self, index: int, element: MusicElement) -> 'MusicSequence':
        """Insert a music element at the specified position.
        
        Args:
            index: The position to insert at
            element: The music element to insert
            
        Returns:
            self for method chaining
        """
        self.elements.insert(index, element)
        self._update_duration()
        return self
    
    def __getitem__(self, index: int) -> MusicElement:
        """Get a music element by index."""
        return self.elements[index]
    
    def __setitem__(self, index: int, element: MusicElement) -> None:
        """Set a music element at the specified index."""
        self.elements[index] = element
        self._update_duration()
    
    def __delitem__(self, index: int) -> None:
        """Delete a music element at the specified index."""
        del self.elements[index]
        self._update_duration()
    
    def __len__(self) -> int:
        """Get the number of elements in the sequence."""
        return len(self.elements)
    
    def __iter__(self) -> Iterator[MusicElement]:
        """Iterate over the music elements."""
        return iter(self.elements)
    
    def __add__(self, other: Union[MusicElement, List[MusicElement]]) -> 'MusicSequence':
        """Concatenate this sequence with another sequence or element."""
        if isinstance(other, list):
            return MusicSequence(self.elements + other)
        elif isinstance(other, MusicElement):
            return MusicSequence(self.elements + [other])
        else:
            raise TypeError(f"Cannot concatenate MusicSequence with {type(other).__name__}")
    
    def __radd__(self, other: Union[MusicElement, List[MusicElement]]) -> 'MusicSequence':
        """Concatenate a sequence or element with this sequence."""
        if isinstance(other, list):
            return MusicSequence(other + self.elements)
        elif isinstance(other, MusicElement):
            return MusicSequence([other] + self.elements)
        else:
            raise TypeError(f"Cannot concatenate {type(other).__name__} with MusicSequence")
    
    def __mul__(self, n: int) -> 'MusicSequence':
        """Repeat this sequence n times."""
        if not isinstance(n, int):
            raise TypeError(f"Can't multiply MusicSequence by non-integer of type '{type(n).__name__}'")
        return MusicSequence(self.elements * n)
    
    def __rmul__(self, n: int) -> 'MusicSequence':
        """Repeat this sequence n times."""
        return self * n
    
    def to_lilypond(self) -> str:
        """Convert the sequence to LilyPond syntax."""
        return " ".join(element.to_lilypond() for element in self.elements)
    
    def to_manim(self):
        """Convert the sequence to a Manim object."""
        # This will be implemented when we integrate with Manim
        pass
    
    def copy(self) -> 'MusicSequence':
        """Create a copy of this sequence."""
        return MusicSequence(
            elements=[element.copy() for element in self.elements],
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )

class Voice(MusicSequence):
    """A voice is a sequence of music elements that can be played by a single instrument or voice."""
    
    def __init__(
        self,
        name: str = "",
        clef: Optional[Clef] = None,
        elements: Optional[List[MusicElement]] = None,
        **kwargs
    ):
        """Initialize a Voice.
        
        Args:
            name: Name of the voice
            clef: The clef to use for this voice (default: Treble)
            elements: Initial list of music elements in this voice
        """
        super().__init__(elements=elements, **kwargs)
        self.name = name
        self.clef = clef if clef is not None else TrebleClef()
    
    def to_lilypond(self) -> str:
        """Convert the voice to LilyPond syntax."""
        lines = [
            f'\\new Voice = "{self.name}" {{',
            f"    {self.clef.to_lilypond()}",
            f"    {super().to_lilypond()}",
            "}"
        ]
        return "\n".join(lines)
    
    def copy(self) -> 'Voice':
        """Create a copy of this voice."""
        return Voice(
            name=self.name,
            clef=self.clef.copy(),
            elements=[element.copy() for element in self.elements],
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )
