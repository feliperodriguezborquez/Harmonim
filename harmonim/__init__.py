"""
Harmonim - A library for creating animated music scores inspired by Manim.

This library provides tools to create and animate music scores programmatically,
supporting various input formats and output renderers.
"""

__version__ = "0.1.0"

# Public API surface for the simplified build
from .renderers.manim_renderer import ManimRenderer
from .renderers.verovio_renderer import VerovioRenderer
from .core.animator import MusicXMLAnimator
from .io.musicxml import MusicXMLParser
from .elements.note import Note, Rest
from .elements.staff import Staff, StaffGroup

__all__ = [
    'Note', 'Rest', 'Staff', 'StaffGroup',
    'ManimRenderer', 'VerovioRenderer',
    'MusicXMLAnimator', 'MusicXMLParser'
]
