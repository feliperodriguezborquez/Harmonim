"""
Staff classes for Harmonim.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Tuple

from .base import MusicElement
from .clef import Clef, TrebleClef
from .key_signature import KeySignature
from .time_signature import TimeSignature
from .barline import Barline
from ..core.utils import Color

class Staff(MusicElement):
    """Represents a musical staff."""
    
    def __init__(
        self,
        clef: Optional[Clef] = None,
        key_signature: Optional[KeySignature] = None,
        time_signature: Optional[TimeSignature] = None,
        elements: Optional[List[MusicElement]] = None,
        **kwargs
    ):
        """Initialize a Staff.
        
        Args:
            clef: The clef to use for this staff (default: Treble)
            key_signature: The key signature (default: C major)
            time_signature: The time signature (default: 4/4)
            elements: Initial list of music elements in this staff
        """
        super().__init__(**kwargs)
        self.clef = clef if clef is not None else TrebleClef()
        self.key_signature = key_signature if key_signature is not None else KeySignature('C')
        self.time_signature = time_signature if time_signature is not None else TimeSignature(4, 4)
        self.elements = elements if elements is not None else []
        
        # Duration is the sum of all elements' durations
        self._update_duration()
    
    def _update_duration(self) -> None:
        """Update the total duration of the staff based on its elements."""
        self.duration = sum(element.duration for element in self.elements)
    
    def add_element(self, element: MusicElement) -> 'Staff':
        """Add a music element to the staff.
        
        Args:
            element: The music element to add
            
        Returns:
            self for method chaining
        """
        self.elements.append(element)
        self._update_duration()
        return self
    
    def add_elements(self, *elements: MusicElement) -> 'Staff':
        """Add multiple music elements to the staff.
        
        Args:
            *elements: Music elements to add
            
        Returns:
            self for method chaining
        """
        self.elements.extend(elements)
        self._update_duration()
        return self
    
    def add_barline(self, barline_type: Optional[Barline] = None) -> 'Staff':
        """Add a barline to the staff.
        
        Args:
            barline_type: The type of barline to add (default: single barline)
            
        Returns:
            self for method chaining
        """
        if barline_type is None:
            barline_type = Barline()
        self.add_element(barline_type)
        return self
    
    def add_measure(self, *elements: MusicElement, barline: bool = True) -> 'Staff':
        """Add a measure with the given elements.
        
        Args:
            *elements: Music elements to add to the measure
            barline: Whether to add a barline after the measure
            
        Returns:
            self for method chaining
        """
        self.add_elements(*elements)
        if barline:
            self.add_barline()
        return self
    
    def to_lilypond(self, id_mapping: Optional[Dict[MusicElement, str]] = None) -> str:
        """Convert the staff to LilyPond syntax.
        
        Args:
            id_mapping: Dictionary mapping elements to SVG IDs.
        """
        # Start with the staff definition
        lines = [
            "\\new Staff { ",
            f"    {self.clef.to_lilypond()}",
            f"    {self.key_signature.to_lilypond()}",
            f"    {self.time_signature.to_lilypond()}"
        ]
        
        # Add all elements
        for element in self.elements:
            svg_id = id_mapping.get(element) if id_mapping else None
            lines.append(f"    {element.to_lilypond(svg_id=svg_id)}")
        
        # Close the staff
        lines.append("}")
        
        return "\n".join(lines)
    
    def to_manim(self):
        """Convert the staff to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def copy(self) -> 'Staff':
        """Create a copy of this staff."""
        return Staff(
            clef=self.clef.copy(),
            key_signature=self.key_signature.copy(),
            time_signature=self.time_signature.copy(),
            elements=[element.copy() for element in self.elements],
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )

class StaffGroup(MusicElement):
    """Represents a group of staves that should be played simultaneously."""
    
    def __init__(
        self,
        staves: Optional[List[Staff]] = None,
        is_simultaneous: bool = True,
        **kwargs
    ):
        """Initialize a StaffGroup.
        
        Args:
            staves: Initial list of staves in this group
            is_simultaneous: Whether the staves should be played simultaneously
        """
        super().__init__(**kwargs)
        self.staves = staves if staves is not None else []
        self.is_simultaneous = is_simultaneous
        
        # Duration is the maximum of all staves' durations
        self._update_duration()
    
    def _update_duration(self) -> None:
        """Update the total duration of the staff group based on its staves."""
        if not self.staves:
            self.duration = 0.0
        else:
            self.duration = max(staff.duration for staff in self.staves)
    
    def add_staff(self, staff: Staff) -> 'StaffGroup':
        """Add a staff to the group.
        
        Args:
            staff: The staff to add
            
        Returns:
            self for method chaining
        """
        self.staves.append(staff)
        self._update_duration()
        return self
    
    def to_lilypond(self, id_mapping: Optional[Dict[MusicElement, str]] = None) -> str:
        """Convert the staff group to LilyPond syntax.
        
        Args:
            id_mapping: Dictionary mapping elements to SVG IDs.
        """
        if not self.staves:
            return ""
            
        if len(self.staves) == 1:
            return self.staves[0].to_lilypond(id_mapping=id_mapping)
            
        # For multiple staves, use a \score block
        lines = [
            "<<",
            "    \\new StaffGroup <<"
        ]
        
        for staff in self.staves:
            staff_lines = staff.to_lilypond(id_mapping=id_mapping).split('\n')
            # Indent all lines
            staff_lines = [f"        {line}" for line in staff_lines]
            lines.extend(staff_lines)
        
        lines.extend([
            "    >>",
            ">>"
        ])
        
        return "\n".join(lines)
    
    def to_manim(self):
        """Convert the staff group to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def copy(self) -> 'StaffGroup':
        """Create a copy of this staff group."""
        return StaffGroup(
            staves=[staff.copy() for staff in self.staves],
            is_simultaneous=self.is_simultaneous,
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )
