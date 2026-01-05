"""
Base renderer classes for Harmonim.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pathlib import Path

from ..core.utils import Color

T = TypeVar('T')

@dataclass
class RenderOptions:
    """Options for rendering musical elements."""
    
    # Output options
    output_dir: str = "output"
    filename: str = "score"
    format: str = "pdf"  # pdf, png, svg, etc.
    
    # Layout options
    page_size: str = "a4"
    page_orientation: str = "portrait"  # or "landscape"
    
    # Staff options
    staff_size: float = 20.0  # in points
    
    # Spacing options
    line_width: float = 0.4  # in mm
    
    # Color options
    color: Optional[Color] = None
    background_color: Optional[Color] = None
    
    # Debug options
    debug: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to a dictionary."""
        return {
            'output_dir': self.output_dir,
            'filename': self.filename,
            'format': self.format,
            'page_size': self.page_size,
            'page_orientation': self.page_orientation,
            'staff_size': self.staff_size,
            'line_width': self.line_width,
            'color': self.color.to_hex() if self.color else None,
            'background_color': self.background_color.to_hex() if self.background_color else None,
            'debug': self.debug
        }
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create options from a dictionary."""
        from ..core.utils import Color
        
        color = None
        if 'color' in data and data['color'] is not None:
            color = Color.from_hex(data['color'])
        
        background_color = None
        if 'background_color' in data and data['background_color'] is not None:
            background_color = Color.from_hex(data['background_color'])
        
        return cls(
            output_dir=data.get('output_dir', 'output'),
            filename=data.get('filename', 'score'),
            format=data.get('format', 'pdf'),
            page_size=data.get('page_size', 'a4'),
            page_orientation=data.get('page_orientation', 'portrait'),
            staff_size=float(data.get('staff_size', 20.0)),
            line_width=float(data.get('line_width', 0.4)),
            color=color,
            background_color=background_color,
            debug=bool(data.get('debug', False))
        )

@dataclass
class RenderContext:
    """Context for rendering musical elements."""
    
    # Current position in the score (in beats)
    time: float = 0.0
    
    # Current staff and voice
    staff: Optional[Any] = None
    voice: Optional[Any] = None
    
    # Current clef, key signature, and time signature
    clef: Optional[Any] = None
    key_signature: Optional[Any] = None
    time_signature: Optional[Any] = None
    
    # Current position in the measure (in beats)
    measure_position: float = 0.0
    
    # Current bar number
    bar_number: int = 1
    
    # Stack for nested contexts (e.g., for voices, chords, etc.)
    _stack: List[Dict[str, Any]] = field(default_factory=list)
    
    def push(self) -> None:
        """Push the current context onto the stack."""
        self._stack.append({
            'time': self.time,
            'staff': self.staff,
            'voice': self.voice,
            'clef': self.clef,
            'key_signature': self.key_signature,
            'time_signature': self.time_signature,
            'measure_position': self.measure_position,
            'bar_number': self.bar_number
        })
    
    def pop(self) -> None:
        """Pop the most recent context from the stack."""
        if not self._stack:
            return
            
        ctx = self._stack.pop()
        self.time = ctx['time']
        self.staff = ctx['staff']
        self.voice = ctx['voice']
        self.clef = ctx['clef']
        self.key_signature = ctx['key_signature']
        self.time_signature = ctx['time_signature']
        self.measure_position = ctx['measure_position']
        self.bar_number = ctx['bar_number']
    
    def copy(self) -> 'RenderContext':
        """Create a copy of this context."""
        ctx = RenderContext()
        ctx.time = self.time
        ctx.staff = self.staff
        ctx.voice = self.voice
        ctx.clef = self.clef
        ctx.key_signature = self.key_signature
        ctx.time_signature = self.time_signature
        ctx.measure_position = self.measure_position
        ctx.bar_number = self.bar_number
        ctx._stack = [dict(s) for s in self._stack]
        return ctx

class Renderer(ABC):
    """Base class for all renderers."""
    
    def __init__(self, options: Optional[RenderOptions] = None):
        """Initialize the renderer.
        
        Args:
            options: Render options
        """
        self.options = options if options is not None else RenderOptions()
        self.context = RenderContext()
    
    @abstractmethod
    def render(self, element: Any, **kwargs) -> Any:
        """Render a musical element.
        
        Args:
            element: The musical element to render
            **kwargs: Additional render options
            
        Returns:
            The rendered output (format depends on the renderer)
        """
        pass
    
    def save(self, output: Any, path: Optional[Union[str, Path]] = None) -> Path:
        """Save the rendered output to a file.
        
        Args:
            output: The rendered output (format depends on the renderer)
            path: Output file path (if None, use options.filename)
            
        Returns:
            The path to the saved file
        """
        if path is None:
            path = Path(self.options.output_dir) / f"{self.options.filename}.{self.options.format}"
        else:
            path = Path(path)
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(output, str):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(output)
        elif hasattr(output, 'save'):
            output.save(path)
        else:
            with open(path, 'wb') as f:
                f.write(output)
        
        return path
    
    def get_context(self) -> RenderContext:
        """Get the current render context."""
        return self.context
    
    def set_context(self, context: RenderContext) -> None:
        """Set the current render context."""
        self.context = context
    
    def push_context(self) -> None:
        """Push the current context onto the stack."""
        self.context.push()
    
    def pop_context(self) -> None:
        """Pop the most recent context from the stack."""
        self.context.pop()
    
    def with_context(self, **kwargs) -> 'Renderer':
        """Create a new renderer with updated context."""
        new_renderer = self.__class__(self.options)
        new_context = self.context.copy()
        
        for key, value in kwargs.items():
            if hasattr(new_context, key):
                setattr(new_context, key, value)
        
        new_renderer.set_context(new_context)
        return new_renderer
