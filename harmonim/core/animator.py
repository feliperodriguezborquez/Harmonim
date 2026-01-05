"""
Animator for Harmonim.
"""
from typing import Any, List, Union
from manim import Animation, AnimationGroup, Succession, ApplyMethod, Wait, RED, BLUE, Create, VMobject
from ..elements.staff import Staff, StaffGroup
from ..elements.note import Note, Rest
from ..renderers.manim_renderer import ManimRenderer

class MusicXMLAnimator:
    """Generates animations from a StaffGroup."""
    
    def __init__(self, staff_group: StaffGroup, renderer: ManimRenderer):
        self.staff_group = staff_group
        self.renderer = renderer
        
    def create_animation(self, color: Any = BLUE) -> Animation:
        """Create an animation that colors notes as they are played."""
        
        # Handle single Staff or StaffGroup
        staves = []
        if isinstance(self.staff_group, StaffGroup):
            staves = self.staff_group.staves
        elif isinstance(self.staff_group, Staff):
            staves = [self.staff_group]
            
        # Collect all elements from all staves into a single timeline
        all_elements = []
        for staff in staves:
            all_elements.extend(staff.elements)
            
        # Sort elements by offset
        sorted_elements = sorted(all_elements, key=lambda x: getattr(x, 'offset', 0.0))
        
        if not sorted_elements:
            return Wait(run_time=1)
            
        # Group by offset
        groups = {}
        for element in sorted_elements:
            off = getattr(element, 'offset', 0.0)
            if off not in groups:
                groups[off] = []
            groups[off].append(element)
        
        sorted_offsets = sorted(groups.keys())
        
        anim_sequence = []
        last_offset = 0.0
        
        for current_offset in sorted_offsets:
            # Wait until this offset
            wait_duration = current_offset - last_offset
            if wait_duration > 0:
                anim_sequence.append(Wait(run_time=wait_duration))
            
            # Get elements at this offset
            elements_at_offset = groups[current_offset]
            
            # Create animations for these elements
            group_anims = []
            
            for element in elements_at_offset:
                # Get rendered object(s) - could be multiple mobjects for chords
                mobjects = []
                
                # Check for direct element mapping (order-based) - could be multiple mobjects
                if hasattr(self.renderer, 'element_to_mobjects'):
                    mobjects_list = self.renderer.element_to_mobjects.get(element, [])
                    if mobjects_list:
                        mobjects = mobjects_list if isinstance(mobjects_list, list) else [mobjects_list]
                        print(f"DEBUG: Found {len(mobjects)} mobject(s) via element_to_mobjects for element at offset {element.offset}")
                
                # Fallback: single mobject mapping
                if not mobjects and hasattr(self.renderer, 'element_to_mobject'):
                    single_mob = self.renderer.element_to_mobject.get(element)
                    if single_mob:
                        mobjects = [single_mob]
                
                # Fallback: ID-based mapping
                if not mobjects and hasattr(self.renderer, 'id_to_mobject') and hasattr(element, 'id') and element.id:
                    mobject = self.renderer.id_to_mobject.get(element.id)
                    if mobject:
                        mobjects = [mobject]
                
                # Fallback: object-based mapping (ManimRenderer)
                if not mobjects:
                    mobject = self.renderer.rendered_elements_map.get(element)
                    if mobject:
                        mobjects = [mobject]
                
                # Animate all mobjects for this element
                for mobject in mobjects:
                    if isinstance(element, (Note, Rest)):
                        # Handle both single mobjects and groups
                        mobs_to_color = []
                        if isinstance(mobject, list):
                            mobs_to_color = mobject
                        else:
                            mobs_to_color = [mobject]
                        
                        # Color each mobject and all its submobjects recursively
                        def color_recursive(mob):
                            # Apply solid color to this mobject
                            anims = []
                            # If it's a VMobject (has fill/stroke)
                            if isinstance(mob, VMobject):
                                anims.append(ApplyMethod(mob.set_fill, color, 1.0, run_time=0.01))
                                anims.append(ApplyMethod(mob.set_stroke, color, 2, run_time=0.01))
                            
                            for sub in mob.submobjects:
                                anims.extend(color_recursive(sub))
                            return anims

                        for mob in mobs_to_color:
                            group_anims.extend(color_recursive(mob))
                        
                        # Handle Ties and Slurs (Instant coloring)
                        if isinstance(element, Note):
                            # Ties
                            if element.tie_start and element.tie_id:
                                # Try to find tie mobject
                                tie_mob = None
                                if hasattr(self.renderer, 'id_to_mobject'):
                                    pass
                                elif hasattr(self.renderer, 'rendered_elements_map'):
                                     pass
                                     
                            # Slurs
                            if element.slur_start and element.slur_id:
                                pass
            
            if group_anims:
                # Play all animations for this timestamp together
                anim_sequence.append(AnimationGroup(*group_anims, lag_ratio=0))
            
            last_offset = current_offset
        
        # Wait for the duration of the last group
        if sorted_offsets:
            last_group = groups[sorted_offsets[-1]]
            last_dur = max((e.duration for e in last_group), default=0.0)
            if last_dur > 0:
                 anim_sequence.append(Wait(run_time=last_dur))

        if not anim_sequence:
            return Wait(run_time=1)
            
        return Succession(*anim_sequence)
