"""
Animation system for Harmonim.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic, Union
import numpy as np
from .utils import logger, clamp

T = TypeVar('T')

class Animatable(ABC):
    """Base class for all animatable objects."""
    
    @abstractmethod
    def interpolate(self, other: 'Animatable', alpha: float) -> 'Animatable':
        """Interpolate between this object and another object.
        
        Args:
            other: The other object to interpolate to.
            alpha: Interpolation factor (0.0 = self, 1.0 = other)
            
        Returns:
            A new object representing the interpolated state.
        """
        pass

@dataclass
class Animation(ABC):
    """Base class for all animations."""
    run_time: float = 1.0
    rate_func: Callable[[float], float] = lambda t: t
    
    @abstractmethod
    def interpolate(self, mobject: Any, alpha: float) -> None:
        """Update the mobject based on the animation progress.
        
        Args:
            mobject: The object to animate.
            alpha: Animation progress (0.0 to 1.0).
        """
        pass
    
    def update_mobject(self, mobject: Any, alpha: float) -> None:
        """Update the mobject with the current animation state."""
        alpha = clamp(alpha, 0.0, 1.0)
        t = self.rate_func(alpha)
        self.interpolate(mobject, t)

class Transform(Animation):
    """Transform one object into another."""
    
    def __init__(
        self, 
        target: Any,
        run_time: float = 1.0,
        rate_func: Callable[[float], float] = lambda t: t,
        **kwargs
    ):
        super().__init__(run_time=run_time, rate_func=rate_func)
        self.target = target
        self.kwargs = kwargs
    
    def interpolate(self, mobject: Any, alpha: float) -> None:
        if hasattr(mobject, 'interpolate') and hasattr(self.target, 'interpolate'):
            mobject.interpolate(self.target, alpha)
        # Add more specific interpolation logic here

class FadeIn(Animation):
    """Fade in an object."""
    
    def __init__(
        self, 
        run_time: float = 0.5,
        rate_func: Callable[[float], float] = lambda t: t,
        **kwargs
    ):
        super().__init__(run_time=run_time, rate_func=rate_func)
        self.kwargs = kwargs
    
    def interpolate(self, mobject: Any, alpha: float) -> None:
        if hasattr(mobject, 'set_opacity'):
            mobject.set_opacity(alpha)

class FadeOut(FadeIn):
    """Fade out an object."""
    
    def interpolate(self, mobject: Any, alpha: float) -> None:
        if hasattr(mobject, 'set_opacity'):
            mobject.set_opacity(1.0 - alpha)

class AnimationGroup(Animation):
    """A group of animations that can be played together."""
    
    def __init__(
        self, 
        *animations: Animation,
        run_time: Optional[float] = None,
        lag_ratio: float = 0.0,
        **kwargs
    ):
        self.animations = list(animations)
        self.lag_ratio = lag_ratio
        
        if run_time is None:
            run_time = max((anim.run_time for anim in self.animations), default=0.0)
        
        super().__init__(run_time=run_time, **kwargs)
    
    def interpolate(self, alpha: float) -> None:
        n_anims = len(self.animations)
        if n_anims == 0:
            return
            
        lag_ratio = self.lag_ratio
        full_lag_time = self.run_time * lag_ratio
        full_anim_time = self.run_time - full_lag_time
        
        for i, anim in enumerate(self.animations):
            anim_alpha = 0.0
            if full_anim_time > 0:
                start_time = (i / n_anims) * full_lag_time
                end_time = start_time + anim.run_time
                anim_alpha = clamp(
                    (alpha * self.run_time - start_time) / (end_time - start_time),
                    0.0,
                    1.0
                )
            
            anim.update_mobject(anim.mobject, anim_alpha)

class Succession(AnimationGroup):
    """Play animations in sequence."""
    
    def __init__(self, *animations: Animation, lag_ratio: float = 1.0, **kwargs):
        super().__init__(*animations, lag_ratio=lag_ratio, **kwargs)

class AnimationBuilder:
    """Builder pattern for creating complex animations."""
    
    def __init__(self, mobject: Any):
        self.mobject = mobject
        self.animations: List[Animation] = []
    
    def add_animation(self, animation: Animation) -> 'AnimationBuilder':
        """Add an animation to the sequence."""
        self.animations.append(animation)
        return self
    
    def fade_in(self, **kwargs) -> 'AnimationBuilder':
        """Add a fade in animation."""
        return self.add_animation(FadeIn(**kwargs))
    
    def fade_out(self, **kwargs) -> 'AnimationBuilder':
        """Add a fade out animation."""
        return self.add_animation(FadeOut(**kwargs))
    
    def transform_to(self, target: Any, **kwargs) -> 'AnimationBuilder':
        """Add a transform animation."""
        return self.add_animation(Transform(target, **kwargs))
    
    def build(self) -> Animation:
        """Build the animation sequence."""
        if not self.animations:
            raise ValueError("No animations added to the builder.")
        
        if len(self.animations) == 1:
            return self.animations[0]
        
        return AnimationGroup(*self.animations)

def animate(mobject: Any) -> AnimationBuilder:
    """Create an animation builder for the given mobject."""
    return AnimationBuilder(mobject)
