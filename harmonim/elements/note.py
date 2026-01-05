"""
Note and Rest classes for Harmonim.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any

from .base import PositionedElement, MusicElement
from ..core.utils import Color

# Duration values for common note types
DURATION_WHOLE = 4.0
DURATION_HALF = 2.0
DURATION_QUARTER = 1.0
DURATION_EIGHTH = 0.5
DURATION_SIXTEENTH = 0.25
DURATION_THIRTY_SECOND = 0.125
DURATION_SIXTY_FOURTH = 0.0625

# Tuplet durations
DURATION_TRIPLET = 2/3  # For eighth note triplets, etc.
DURATION_QUINTUPLET = 4/5  # For quintuplets

class Note(PositionedElement):
    """A musical note."""
    
    def __init__(
        self,
        pitch: Optional[Union[str, float, List[Union[str, float]]]] = None,
        duration: float = DURATION_QUARTER,
        octave: Optional[int] = None,
        accidental: Optional[str] = None,
        dot: bool = False,
        articulation: Optional[str] = None,
        dynamic: Optional[str] = None,
        tie_start: bool = False,
        tie_stop: bool = False,
        slur_start: bool = False,
        slur_stop: bool = False,
        tie_id: Optional[str] = None,
        slur_id: Optional[str] = None,
        tie_duration: float = 0.0,
        slur_duration: float = 0.0,
        ids: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize a Note."""
        
        self.pitches_data = []
        
        # Helper to parse a single pitch
        def parse_single_pitch(p, default_oct=None, default_acc=None):
            pos = 0.0
            oct_val = 4
            acc_val = default_acc
            
            if isinstance(p, str):
                # Parse scientific pitch notation (e.g., 'C4', 'A#3')
                if p and p[0].isalpha():
                    pitch_name = p[0].upper()
                    curr_p = p
                    if len(curr_p) > 1 and curr_p[1] in ['#', 'b']:
                        accidental_char = curr_p[1]
                        curr_p = curr_p[2:]
                        acc_val = {
                            '#': 'sharp',
                            'b': 'flat',
                            '##': 'double-sharp',
                            'bb': 'double-flat'
                        }.get(accidental_char, acc_val)
                    else:
                        pitch_name = curr_p[0].upper()
                        curr_p = curr_p[1:]
                    
                    # Find octave if present
                    if curr_p and curr_p[0].isdigit():
                        oct_val = int(curr_p[0])
                    elif default_oct is not None:
                        oct_val = default_oct
                    
                    # Calculate position
                    pitch_classes = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}
                    pos = pitch_classes[pitch_name] + (oct_val - 4) * 7
                else:
                    try:
                        pos = float(p)
                        oct_val = 4 + int(pos // 7)
                    except ValueError:
                        raise ValueError(f"Invalid pitch: {p}")
            else:
                pos = float(p)
                if default_oct is not None:
                    oct_val = default_oct
                else:
                    oct_val = 4 + int(pos // 7)
            
            return {'position': pos, 'octave': oct_val, 'accidental': acc_val}

        # Handle pitch input
        primary_position = 0.0
        primary_octave = 4
        primary_accidental = accidental

        if pitch is not None:
            if isinstance(pitch, list):
                for p in pitch:
                    data = parse_single_pitch(p, octave, accidental)
                    self.pitches_data.append(data)
                
                # Use the first pitch as primary for PositionedElement (or maybe the highest?)
                if self.pitches_data:
                    primary_position = self.pitches_data[0]['position']
                    primary_octave = self.pitches_data[0]['octave']
                    primary_accidental = self.pitches_data[0]['accidental']
            else:
                data = parse_single_pitch(pitch, octave, accidental)
                self.pitches_data.append(data)
                primary_position = data['position']
                primary_octave = data['octave']
                primary_accidental = data['accidental']
        
        # Set default octave if not provided (and not set by parsing)
        if octave is None and not self.pitches_data:
             # Fallback
             pass
        
        # Apply dot if needed
        if dot:
            duration *= 1.5
        
        super().__init__(
            position=primary_position,
            octave=primary_octave,
            accidental=primary_accidental,
            duration=duration,
            **kwargs
        )
        
        self.dot = dot
        self.articulation = articulation
        self.dynamic = dynamic
        self.tie_start = tie_start
        self.tie_stop = tie_stop
        self.slur_start = slur_start
        self.slur_stop = slur_stop
        self.tie_id = tie_id
        self.slur_id = slur_id
        self.tie_duration = tie_duration
        self.slur_duration = slur_duration
        self.ids = ids or []
    
    def _data_to_lilypond_pitch(self, data) -> str:
        """Convert pitch data to LilyPond syntax."""
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
        
        # Calculate pitch name from position
        positions = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        # position is relative to C4 (0)
        # We need to reconstruct the pitch name from position and octave
        # But wait, position = pitch_class_idx + (octave - 4) * 7
        # So pitch_class_idx = position % 7 (if position is int-ish)
        
        pos = data['position']
        octave = data['octave']
        acc = data['accidental']
        
        # Re-derive pitch name
        # We stored position which includes octave info, but we also stored octave explicitly.
        # Let's use the position to get the note name index.
        # Note: position might be float.
        idx = int(round(pos)) % 7
        # Handle negative positions correctly? % 7 in python handles negatives.
        base_pitch = positions[idx]
        
        octave_offset = octave - 4
        
        pitch_str = pitch_map[base_pitch]
        acc_str = accidental_map.get(acc, '')
        
        pitch_str += acc_str
        
        if octave_offset > 0:
            pitch_str += "'" * octave_offset
        elif octave_offset < 0:
            pitch_str += "," * abs(octave_offset)
            
        return pitch_str

    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the note to LilyPond syntax."""
        
        # Get pitch string
        if len(self.pitches_data) > 1:
            # Chord
            pitch_str = "<"
            for p_data in self.pitches_data:
                pitch_str += " " + self._data_to_lilypond_pitch(p_data)
            pitch_str += " >"
        elif self.pitches_data:
            pitch_str = self._data_to_lilypond_pitch(self.pitches_data[0])
        else:
            pitch_str = "c" # Fallback
        
        # Get duration string
        duration_map = {
            4.0: '1',
            2.0: '2',
            1.0: '4',
            0.5: '8',
            0.25: '16',
            0.125: '32',
            0.0625: '64',
        }
        
        # Find the closest standard duration
        std_durations = sorted(duration_map.keys())
        closest_dur = min(std_durations, key=lambda x: abs(x - self.duration))
        
        # Calculate the multiplier for tuplets
        multiplier = self.duration / closest_dur
        
        # Handle tuplets
        tuplet = ""
        if abs(multiplier - 2/3) < 0.01:  # Triplet
            tuplet = "\\times 2/3 { "
        elif abs(multiplier - 4/5) < 0.01:  # Quintuplet
            tuplet = "\\times 4/5 { "
        
        duration = duration_map[closest_dur]
        
        # Add dot if needed
        if self.dot:
            duration += "."
        
        # Add articulation
        articulation = ""
        if self.articulation:
            articulations = {
                'staccato': r'\staccato',
                'tenuto': r'\tenuto',
                'accent': r'\accent',
                'marcato': r'\marcato',
                'fermata': r'\fermata',
                'trill': r'\trill',
                'mordent': r'\mordent',
                'turn': r'\turn',
                'upbow': r'\upbow',
                'downbow': r'\downbow',
            }
            articulation = articulations.get(self.articulation.lower(), '')
        
        # Add dynamic
        dynamic = f"\\{self.dynamic} " if self.dynamic else ""
        
        # Build the note string
        note_str = f"{pitch_str}{duration}{articulation}"
        
        # Add ID tweak if provided
        if svg_id:
            note_str = f"\\tweak output-attributes #'((id . \"{svg_id}\")) {note_str}"
            
        # Add Tie
        if self.tie_start:
            if self.tie_id:
                note_str += f" \\tweak output-attributes #'((id . \"{self.tie_id}\")) ~"
            else:
                note_str += " ~"
                
        # Add Slur Start
        if self.slur_start:
            if self.slur_id:
                note_str += f" \\tweak output-attributes #'((id . \"{self.slur_id}\")) ("
            else:
                note_str += " ("
                
        # Add Slur Stop
        if self.slur_stop:
            note_str += " )"
        
        # Add tuplet if needed
        if tuplet:
            note_str = f"{tuplet}{note_str} }}"
        
        # Add dynamic if present
        if dynamic:
            note_str = f"{note_str} {dynamic}"
        
        return note_str
    
    def to_manim(self):
        """Convert the note to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def copy(self) -> 'Note':
        """Create a copy of this note."""
        return Note(
            pitch=self.position,
            duration=self.duration,
            octave=self.octave,
            accidental=self.accidental,
            dot=self.dot,
            articulation=self.articulation,
            dynamic=self.dynamic,
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )

class Rest(MusicElement):
    """A musical rest."""
    
    def __init__(
        self,
        duration: float = DURATION_QUARTER,
        dot: bool = False,
        **kwargs
    ):
        """Initialize a Rest.
        
        Args:
            duration: Duration of the rest in beats (1.0 = quarter rest, 4.0 = whole rest, etc.)
            dot: Whether the rest is dotted (increases duration by 50%)
        """
        # Apply dot if needed
        if dot:
            duration *= 1.5
        
        super().__init__(duration=duration, **kwargs)
        self.dot = dot
    
    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the rest to LilyPond syntax.
        
        Args:
            svg_id: Optional ID to assign to the SVG element (for animation mapping).
        """
        duration_map = {
            4.0: 'r1',
            2.0: 'r2',
            1.0: 'r4',
            0.5: 'r8',
            0.25: 'r16',
            0.125: 'r32',
            0.0625: 'r64',
        }
        
        # Find the closest standard duration
        std_durations = sorted(duration_map.keys())
        closest_dur = min(std_durations, key=lambda x: abs(x - self.duration))
        
        # Calculate the multiplier for tuplets
        multiplier = self.duration / closest_dur
        
        # Handle tuplets
        tuplet = ""
        if abs(multiplier - 2/3) < 0.01:  # Triplet
            tuplet = "\\times 2/3 { "
        elif abs(multiplier - 4/5) < 0.01:  # Quintuplet
            tuplet = "\\times 4/5 { "
        
        rest = duration_map[closest_dur]
        
        # Add dot if needed
        if self.dot:
            rest += "."
        
        # Add ID tweak if provided
        if svg_id:
            rest = f"\\tweak output-attributes #'((id . \"{svg_id}\")) {rest}"
        
        # Add tuplet if needed
        if tuplet:
            rest = f"{tuplet}{rest} }}"
        
        return rest
    
    def to_manim(self):
        """Convert the rest to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def copy(self) -> 'Rest':
        """Create a copy of this rest."""
        return Rest(
            duration=self.duration / (1.5 if self.dot else 1.0),
            dot=self.dot,
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )

# Common note durations as class methods for convenience
Note.w = lambda **kwargs: Note(duration=DURATION_WHOLE, **kwargs)
Note.h = lambda **kwargs: Note(duration=DURATION_HALF, **kwargs)
Note.q = lambda **kwargs: Note(duration=DURATION_QUARTER, **kwargs)
Note.e = lambda **kwargs: Note(duration=DURATION_EIGHTH, **kwargs)
Note.s = lambda **kwargs: Note(duration=DURATION_SIXTEENTH, **kwargs)
Note.t = lambda **kwargs: Note(duration=DURATION_THIRTY_SECOND, **kwargs)
Note.x = lambda **kwargs: Note(duration=DURATION_SIXTY_FOURTH, **kwargs)

# Common rests as class methods for convenience
Rest.w = lambda **kwargs: Rest(duration=DURATION_WHOLE, **kwargs)
Rest.h = lambda **kwargs: Rest(duration=DURATION_HALF, **kwargs)
Rest.q = lambda **kwargs: Rest(duration=DURATION_QUARTER, **kwargs)
Rest.e = lambda **kwargs: Rest(duration=DURATION_EIGHTH, **kwargs)
Rest.s = lambda **kwargs: Rest(duration=DURATION_SIXTEENTH, **kwargs)
Rest.t = lambda **kwargs: Rest(duration=DURATION_THIRTY_SECOND, **kwargs)
Rest.x = lambda **kwargs: Rest(duration=DURATION_SIXTY_FOURTH, **kwargs)
