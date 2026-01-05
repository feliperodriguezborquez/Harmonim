"""
Key signature classes for Harmonim.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum, auto

from .base import MusicElement
from ..core.utils import Color

class KeyType(Enum):
    """Enum for major and minor key types."""
    MAJOR = auto()
    MINOR = auto()
    DORIAN = auto()
    PHRYGIAN = auto()
    LYDIAN = auto()
    MIXOLYDIAN = auto()
    AEOLIAN = auto()
    LOCRIAN = auto()

class KeySignature(MusicElement):
    """Represents a key signature in musical notation."""
    
    # Circle of fifths for major and minor keys
    MAJOR_KEYS = [
        'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#',
        'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb'
    ]
    
    MINOR_KEYS = [
        'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#',
        'D', 'G', 'C', 'F', 'Bb', 'Eb', 'Ab'
    ]
    
    # Number of sharps or flats for each key
    KEY_SIGNATURES = {
        # Major keys
        'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6, 'C#': 7,
        'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5, 'Gb': -6, 'Cb': -7,
        # Minor keys
        'Am': 0, 'Em': 1, 'Bm': 2, 'F#m': 3, 'C#m': 4, 'G#m': 5, 'D#m': 6, 'A#m': 7,
        'Dm': -1, 'Gm': -2, 'Cm': -3, 'Fm': -4, 'Bbm': -5, 'Ebm': -6, 'Abm': -7
    }
    
    # Order of sharps and flats
    SHARPS_ORDER = ['F', 'C', 'G', 'D', 'A', 'E', 'B']
    FLATS_ORDER = ['B', 'E', 'A', 'D', 'G', 'C', 'F']
    
    def __init__(
        self,
        key: str = 'C',
        key_type: KeyType = KeyType.MAJOR,
        **kwargs
    ):
        """Initialize a KeySignature.

        Args:
            key: The root note of the key (e.g., 'C', 'G', 'D', etc.)
            key_type: The type of key (major, minor, etc.)
        """
        super().__init__(**kwargs)
        
        self.key_type = key_type
        normalized_key = self._normalize_key_name(key)
        if key_type == KeyType.MAJOR:
            self.key = normalized_key
        else:
            self.key = normalized_key if normalized_key.lower().endswith('m') else f"{normalized_key}m"
        
        # Handle minor keys
        if key_type != KeyType.MAJOR:
            if not self.key.lower().endswith('m'):
                self.key = f"{self.key}m"
        
        # Get the number of sharps or flats
        self.sharps = 0
        self.flats = 0
        
        key_str = self.key
        if key_str in self.KEY_SIGNATURES:
            count = self.KEY_SIGNATURES[key_str]
            if count > 0:
                self.sharps = count
            else:
                self.flats = -count
        else:
            raise ValueError(f"Invalid key: {key_str}")
        
        # Duration is 0 for key signatures (they don't take up time)
        self.duration = 0.0

    @staticmethod
    def _normalize_key_name(key: str) -> str:
        """Standardize user-provided key names (e.g., 'bb' -> 'Bb')."""
        key = (key or '').strip()
        if not key:
            raise ValueError("Key cannot be empty")
        first = key[0].upper()
        rest = key[1:]
        return f"{first}{rest}"
    
    def get_accidentals(self) -> List[Tuple[str, str]]:
        """Get a list of accidentals in this key signature.
        
        Returns:
            A list of tuples (note, accidental) where accidental is 'sharp' or 'flat'
        """
        accidentals = []
        
        if self.sharps > 0:
            for i in range(self.sharps):
                note = self.SHARPS_ORDER[i % len(self.SHARPS_ORDER)]
                accidentals.append((note, 'sharp'))
        elif self.flats > 0:
            for i in range(self.flats):
                note = self.FLATS_ORDER[i % len(self.FLATS_ORDER)]
                accidentals.append((note, 'flat'))
        
        return accidentals
    
    def to_lilypond(self, svg_id: Optional[str] = None) -> str:
        """Convert the key signature to LilyPond syntax."""
        # Handle major/minor
        lily_key = self.key.lower()
        if lily_key.endswith('m'):
            lily_key = lily_key[:-1]
        if self.key_type == KeyType.MAJOR:
            key_str = f"\\key {lily_key} \\major"
        else:
            key_str = f"\\key {lily_key} \\minor"
        
        # Handle mode if not major/minor
        if self.key_type not in (KeyType.MAJOR, KeyType.MINOR):
            mode_map = {
                KeyType.DORIAN: r'\dorian',
                KeyType.PHRYGIAN: r'\phrygian',
                KeyType.LYDIAN: r'\lydian',
                KeyType.MIXOLYDIAN: r'\mixolydian',
                KeyType.AEOLIAN: r'\aeolian',
                KeyType.LOCRIAN: r'\locrian',
            }
            key_str = f"{key_str} {mode_map[self.key_type]}"
        
        return key_str
    
    def to_manim(self):
        """Convert the key signature to a Manim object."""
        from ..renderers.manim_renderer import ManimRenderer
        renderer = ManimRenderer()
        return renderer.render(self)
    
    def get_relative_major(self) -> str:
        """Get the relative major of a minor key, or return self if already major."""
        if self.key_type == KeyType.MAJOR:
            return self.key
        
        # Find the relative major (3 semitones up)
        major_key = self.key.upper()
        if major_key.endswith('M'):
            major_key = major_key[:-1]
        
        # Handle enharmonic equivalents
        enharmonic_map = {
            'B#': 'C', 'C#': 'Db', 'D#': 'Eb', 'E#': 'F',
            'F#': 'Gb', 'G#': 'Ab', 'A#': 'Bb',
            'Cb': 'B', 'D': 'D', 'E': 'E', 'G': 'G', 'A': 'A'
        }
        
        return enharmonic_map.get(major_key, major_key)
    
    def get_relative_minor(self) -> str:
        """Get the relative minor of a major key, or return self if already minor."""
        if self.key_type != KeyType.MAJOR:
            return self.key
        
        # Find the relative minor (3 semitones down)
        minor_key = chr((ord(self.key[0]) - ord('A') + 5) % 7 + ord('a'))
        if len(self.key) > 1 and self.key[1] in ('#', 'b'):
            minor_key += self.key[1]
        
        return minor_key
    
    def transpose(self, steps: int) -> 'KeySignature':
        """Transpose the key signature by the given number of steps.
        
        Args:
            steps: Number of semitones to transpose (positive = up, negative = down)
            
        Returns:
            A new transposed KeySignature
        """
        # Get all keys in order of the circle of fifths
        if self.key_type == KeyType.MAJOR:
            keys = self.MAJOR_KEYS
        else:
            keys = self.MINOR_KEYS
        
        # Find current key in the circle
        current_key = self.key.upper()
        if current_key.endswith('M'):
            current_key = current_key[:-1]
        
        try:
            current_idx = keys.index(current_key)
        except ValueError:
            # Handle enharmonic equivalents
            enharmonic_map = {
                'B#': 'C', 'E#': 'F', 'Cb': 'B', 'Fb': 'E',
                'C#': 'Db', 'D#': 'Eb', 'F#': 'Gb', 'G#': 'Ab', 'A#': 'Bb'
            }
            current_key = enharmonic_map.get(current_key, current_key)
            current_idx = keys.index(current_key)
        
        # Calculate new position in the circle
        new_idx = (current_idx + steps) % len(keys)
        new_key = keys[new_idx]
        
        return KeySignature(key=new_key, key_type=self.key_type)
    
    def copy(self) -> 'KeySignature':
        """Create a copy of this key signature."""
        return KeySignature(
            key=self.key.replace('m', '').replace('M', ''),
            key_type=self.key_type,
            color=self.color,
            opacity=self.opacity,
            **self.properties
        )

# Common key signatures for convenience
C_MAJOR = KeySignature('C', KeyType.MAJOR)
G_MAJOR = KeySignature('G', KeyType.MAJOR)
D_MAJOR = KeySignature('D', KeyType.MAJOR)
A_MAJOR = KeySignature('A', KeyType.MAJOR)
E_MAJOR = KeySignature('E', KeyType.MAJOR)
B_MAJOR = KeySignature('B', KeyType.MAJOR)
F_SHARP_MAJOR = KeySignature('F#', KeyType.MAJOR)
C_SHARP_MAJOR = KeySignature('C#', KeyType.MAJOR)
F_MAJOR = KeySignature('F', KeyType.MAJOR)
B_FLAT_MAJOR = KeySignature('Bb', KeyType.MAJOR)
E_FLAT_MAJOR = KeySignature('Eb', KeyType.MAJOR)
A_FLAT_MAJOR = KeySignature('Ab', KeyType.MAJOR)
D_FLAT_MAJOR = KeySignature('Db', KeyType.MAJOR)
G_FLAT_MAJOR = KeySignature('Gb', KeyType.MAJOR)
C_FLAT_MAJOR = KeySignature('Cb', KeyType.MAJOR)

A_MINOR = KeySignature('A', KeyType.MINOR)
E_MINOR = KeySignature('E', KeyType.MINOR)
B_MINOR = KeySignature('B', KeyType.MINOR)
F_SHARP_MINOR = KeySignature('F#', KeyType.MINOR)
C_SHARP_MINOR = KeySignature('C#', KeyType.MINOR)
G_SHARP_MINOR = KeySignature('G#', KeyType.MINOR)
D_SHARP_MINOR = KeySignature('D#', KeyType.MINOR)
A_SHARP_MINOR = KeySignature('A#', KeyType.MINOR)
D_MINOR = KeySignature('D', KeyType.MINOR)
G_MINOR = KeySignature('G', KeyType.MINOR)
C_MINOR = KeySignature('C', KeyType.MINOR)
F_MINOR = KeySignature('F', KeyType.MINOR)
B_FLAT_MINOR = KeySignature('Bb', KeyType.MINOR)
E_FLAT_MINOR = KeySignature('Eb', KeyType.MINOR)
A_FLAT_MINOR = KeySignature('Ab', KeyType.MINOR)
