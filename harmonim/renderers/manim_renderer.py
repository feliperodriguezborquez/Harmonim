"""
Manim renderer for Harmonim.
"""
from typing import Any, Optional, Union, List
from manim import Text, VGroup, Line, UP, DOWN, RIGHT, LEFT, Mobject, ORIGIN, WHITE, BLACK, CubicBezier
import numpy as np

import manimpango

from .base import Renderer, RenderOptions
from ..elements.note import Note, Rest
from ..elements.beam import Beam
from ..elements.tie import Tie
from ..elements.clef import Clef, TrebleClef, BassClef, AltoClef, TenorClef
from ..elements.key_signature import KeySignature
from ..elements.time_signature import TimeSignature
from ..elements.staff import Staff, StaffGroup
from ..core.config import config
from ..core.smufl_map import get_smufl_char

from ..elements.barline import Barline, BarlineType

class ManimRenderer(Renderer):
    """Renderer that converts musical elements to Manim objects."""
    
    def __init__(self, options: Optional[RenderOptions] = None):
        """Initialize the Manim renderer."""
        super().__init__(options)
        # Register font once
        try:
            manimpango.register_font(config.font_path)
        except Exception as e:
            print(f"Warning: Could not register font at {config.font_path}: {e}")
        
        # Constants
        self.staff_line_distance = 0.25 # Distance between staff lines in Manim units
        self.font_size = 64 # Increased from 48 to fill space better
        self.default_color = BLACK
        self.beat_spacing = 2.5 # Spacing per beat (quarter note)
        
        # Engraving defaults (relative to staff space)
        # 1 space = self.staff_line_distance
        # Stem thickness ~ 0.12 spaces
        # Staff line thickness ~ 0.13 spaces
        # Barline thickness ~ 0.16 spaces
        # Beam thickness ~ 0.5 spaces
        
        # Manim stroke_width is in points? Or pixels?
        # It's roughly pixels at default resolution.
        # Let's tune it visually.
        self.staff_line_thickness = 2
        self.stem_thickness = 2.5 # Slightly thicker than staff lines
        self.barline_thickness = 2.5
        self.beam_thickness = 5.0 # Thicker for beams
        self.tie_thickness = 2.0
        
        if options and options.color:
            self.default_color = options.color.to_hex() if hasattr(options.color, 'to_hex') else options.color
            
        # Cache for rendered elements to support linking (like Ties)
        self.rendered_elements_map = {}

    def render(self, element: Any, **kwargs) -> Mobject:
        """Render a musical element to a Manim object."""
        obj = None
        if isinstance(element, Note):
            obj = self.render_note(element, **kwargs)
        elif isinstance(element, Rest):
            obj = self.render_rest(element, **kwargs)
        elif isinstance(element, Beam):
            obj = self.render_beam(element, **kwargs)
        elif isinstance(element, Tie):
            obj = self.render_tie(element, **kwargs)
        elif isinstance(element, Clef):
            obj = self.render_clef(element, **kwargs)
        elif isinstance(element, KeySignature):
            obj = self.render_key_signature(element, **kwargs)
        elif isinstance(element, TimeSignature):
            obj = self.render_time_signature(element, **kwargs)
        elif isinstance(element, Barline):
            obj = self.render_barline(element, **kwargs)
        elif isinstance(element, Staff):
            obj = self.render_staff(element, **kwargs)
        elif isinstance(element, StaffGroup):
            obj = self.render_staff_group(element, **kwargs)
        else:
            raise NotImplementedError(f"Rendering for {type(element).__name__} not implemented")
            
        # Cache the rendered object keyed by the element instance
        self.rendered_elements_map[element] = obj
        return obj

    def render_note(self, note: Note, suppress_stem: bool = False, **kwargs) -> VGroup:
        """Render a Note to a Manim VGroup."""
        group = VGroup()
        
        # Get all pitches
        pitches = note.pitches_data
        if not pitches:
            # Fallback if no pitches data
            pitches = [{'position': note.position, 'octave': note.octave, 'accidental': note.accidental}]

        # Determine notehead char
        if note.duration >= 4.0: # Whole note (semibreve) or larger
             if note.duration >= 8.0:
                 head_char = get_smufl_char('notehead_double_whole')
             else:
                 head_char = get_smufl_char('notehead_whole')
             has_stem = False
        elif note.duration >= 2.0: # Half note (minim)
            head_char = get_smufl_char('notehead_half')
            has_stem = True
        else: # Quarter (crotchet) or shorter
            head_char = get_smufl_char('notehead_black')
            has_stem = True

        if suppress_stem:
            has_stem = False

        # Collect notehead positions and objects
        notehead_objs = []
        note_positions = [] # (staff_pos, x_shift, accidental)
        
        clef = self.context.clef or TrebleClef()
        
        # Calculate staff positions for all pitches
        for p_data in pitches:
            # Calculate pitch name
            idx = int(round(p_data['position'])) % 7
            pitch_name = ['C', 'D', 'E', 'F', 'G', 'A', 'B'][idx]
            
            staff_pos = clef.get_pitch_position(pitch_name, p_data['octave'])
            note_positions.append({'staff_pos': staff_pos, 'accidental': p_data['accidental']})

        # Sort by staff position (ascending)
        note_positions.sort(key=lambda x: x['staff_pos'])
        
        # Determine stem direction
        # Rule: Determine "center" of the chord. If above middle line, stem DOWN. If below, stem UP.
        avg_pos = sum(p['staff_pos'] for p in note_positions) / len(note_positions)
        stem_direction = DOWN if avg_pos >= 0 else UP
        
        min_y = float('inf')
        max_y = float('-inf')
        
        # Render noteheads
        for p in note_positions:
            staff_pos = p['staff_pos']
            y_pos = staff_pos * (self.staff_line_distance / 2)
            
            min_y = min(min_y, y_pos)
            max_y = max(max_y, y_pos)
            
            notehead = Text(head_char, font="Bravura", font_size=self.font_size, color=self.default_color)
            notehead.shift(UP * y_pos)
            group.add(notehead)
            notehead_objs.append(notehead)
            
            # Ledger lines
            if staff_pos > 4:
                for l in range(6, int(staff_pos) + 1, 2):
                    ledger = Line(start=LEFT*0.2, end=RIGHT*0.2, stroke_width=self.staff_line_thickness, color=self.default_color)
                    ledger.move_to(UP * l * (self.staff_line_distance / 2))
                    ledger.match_x(notehead)
                    group.add_to_back(ledger)
            elif staff_pos < -4:
                for l in range(-6, int(staff_pos) - 1, -2):
                    ledger = Line(start=LEFT*0.2, end=RIGHT*0.2, stroke_width=self.staff_line_thickness, color=self.default_color)
                    ledger.move_to(UP * l * (self.staff_line_distance / 2))
                    ledger.match_x(notehead)
                    group.add_to_back(ledger)
                    
            # Accidentals
            if p['accidental']:
                acc_map = {
                    'flat': 'accidental_flat',
                    'natural': 'accidental_natural',
                    'sharp': 'accidental_sharp',
                    'double-sharp': 'accidental_double_sharp',
                    'double-flat': 'accidental_double_flat'
                }
                acc_name = acc_map.get(p['accidental'])
                if acc_name:
                    acc_char = get_smufl_char(acc_name)
                    accidental = Text(acc_char, font="Bravura", font_size=self.font_size, color=self.default_color)
                    accidental.next_to(notehead, LEFT, buff=0.1)
                    accidental.match_y(notehead)
                    group.add(accidental)
                    
            # Dots
            if note.dot:
                dot_char = "\uE4A5" # augmentationDot
                dot = Text(dot_char, font="Bravura", font_size=self.font_size, color=self.default_color)
                
                dot_y = y_pos
                if int(staff_pos) % 2 == 0: # On a line
                    dot_y += (self.staff_line_distance / 2)
                
                # Position dot relative to notehead
                dot.move_to([notehead.get_right()[0] + 0.2, dot_y, 0])
                group.add(dot)

        # Stem
        if has_stem and notehead_objs:
            # Get reference notehead for X position (using the first one)
            ref_note = notehead_objs[0]
            nh_right = ref_note.get_right()[0]
            nh_left = ref_note.get_left()[0]
            
            if stem_direction is UP:
                stem_x = nh_right - 0.01
                # Stem goes from bottom note (min_y) up to top note (max_y) + 3.5 spaces
                stem_end_y = max_y + 3.5 * self.staff_line_distance
                
                stem = Line(
                    start=[stem_x, min_y, 0], 
                    end=[stem_x, stem_end_y, 0], 
                    stroke_width=self.stem_thickness, 
                    color=self.default_color
                )
                group.add(stem)
                
                # Flags
                if note.duration < 1.0:
                    flag_char = ""
                    if note.duration >= 0.5: 
                        flag_char = get_smufl_char('flag_eighth_up')
                    elif note.duration >= 0.25: 
                        flag_char = get_smufl_char('flag_sixteenth_up')
                    
                    if flag_char:
                        flag = Text(flag_char, font="Bravura", font_size=self.font_size, color=self.default_color)
                        flag.move_to(stem.get_end(), aligned_edge=UP+LEFT)
                        flag.shift(DOWN * 0.05 + RIGHT * 0.01) 
                        group.add(flag)
            else:
                stem_x = nh_left + 0.01
                # Stem goes from top note (max_y) down to bottom note (min_y) - 3.5 spaces
                stem_end_y = min_y - 3.5 * self.staff_line_distance
                
                stem = Line(
                    start=[stem_x, max_y, 0], 
                    end=[stem_x, stem_end_y, 0], 
                    stroke_width=self.stem_thickness, 
                    color=self.default_color
                )
                group.add(stem)
                
                # Flags
                if note.duration < 1.0:
                    flag_char = ""
                    if note.duration >= 0.5: 
                        flag_char = get_smufl_char('flag_eighth_down')
                    elif note.duration >= 0.25: 
                        flag_char = get_smufl_char('flag_sixteenth_down')
                    
                    if flag_char:
                        flag = Text(flag_char, font="Bravura", font_size=self.font_size, color=self.default_color)
                        flag.move_to(stem.get_end(), aligned_edge=DOWN+LEFT)
                        flag.shift(UP * 0.05 + RIGHT * 0.01)
                        group.add(flag)

        # Set color
        if hasattr(note, 'color') and note.color:
             group.set_color(note.color.to_hex() if hasattr(note.color, 'to_hex') else note.color)
        
        return group

    def render_beam(self, beam: Beam, **kwargs) -> VGroup:
        """Render a Beam to a Manim VGroup."""
        group = VGroup()
        notes_group = VGroup()
        
        if not beam.notes:
            return group
            
        # 1. Render all notes without stems
        rendered_notes = []
        current_x = 0.0
        
        # Calculate positions
        # We need to know the vertical positions to determine beam slope
        note_positions = [] # (x, y) of notehead center
        
        for note in beam.notes:
            # Render note without stem
            note_obj = self.render_note(note, suppress_stem=True)
            
            # Position horizontally
            # Note: render_note returns object centered at 0 (mostly)
            # We want to shift it to current_x
            note_obj.move_to([current_x, note_obj.get_y(), 0])
            
            rendered_notes.append(note_obj)
            notes_group.add(note_obj)
            
            # Store position of notehead (first element of group usually)
            # render_note returns VGroup(notehead, [dot, accidental...])
            # notehead is index 0
            notehead = note_obj[0]
            note_positions.append(notehead.get_center())
            
            # Advance x
            current_x += note.duration * self.beat_spacing
            
        group.add(notes_group)
        
        # 2. Determine beam direction and placement
        # Simple logic: if average position is above center line, beam down. Else beam up.
        avg_y = sum(p[1] for p in note_positions) / len(note_positions)
        direction = DOWN if avg_y >= 0 else UP
        
        # 3. Calculate beam start and end points
        # Stem length standard is 3.5 spaces.
        # We want the beam to clear the notes.
        # Beam should be at least 3.5 spaces from the furthest notehead in the "wrong" direction?
        # Or just 3.5 spaces from the notehead?
        
        # Let's find the "outermost" note relative to the direction
        # If direction is UP, we want the highest note? No, stems go UP from notehead.
        # So we want the beam to be above the highest note?
        # Actually, if stems are UP, the beam connects the tops of the stems.
        # The stem length is variable to make the beam straight.
        # Standard stem length is 3.5 spaces.
        # Let's try to set the "anchor" stem (usually the one furthest from the beam?) to 3.5 spaces.
        
        # Let's fit a line.
        # Slope: usually follows the general trend of notes, but flattened.
        # For now, let's make it horizontal or follow start/end.
        
        first_pos = note_positions[0]
        last_pos = note_positions[-1]
        
        # Slope based on first and last note
        # Limit slope?
        slope = (last_pos[1] - first_pos[1]) / (last_pos[0] - first_pos[0]) if last_pos[0] != first_pos[0] else 0
        
        # Clamp slope to avoid extreme angles
        max_slope = 0.5 # Arbitrary
        slope = max(-max_slope, min(max_slope, slope))
        
        # Determine Y intercept (start Y)
        # We want the beam to be at least stem_length away from the noteheads.
        stem_length = 3.5 * self.staff_line_distance
        
        # Calculate required Y for each note to satisfy min stem length
        required_ys = []
        for i, pos in enumerate(note_positions):
            x = pos[0]
            y = pos[1]
            # Predicted beam Y at this X: start_beam_y + slope * (x - start_x)
            # We need beam_y >= y + stem_length (if UP)
            # or beam_y <= y - stem_length (if DOWN)
            
            if direction is UP:
                req = y + stem_length
            else:
                req = y - stem_length
            required_ys.append(req)
            
        # Find the "limiting" note (the one that pushes the beam furthest)
        # If UP, we need beam to be above ALL required_ys
        # But we also want to maintain the slope.
        # So we find a start_beam_y such that for all i:
        # start_beam_y + slope * (x_i - x_0) >= req_i (if UP)
        
        # Let beam_y(x) = C + slope * (x - x_0)
        # C >= req_i - slope * (x_i - x_0)
        
        x_0 = first_pos[0]
        
        constraints = []
        for i, req in enumerate(required_ys):
            x_i = note_positions[i][0]
            c_constraint = req - slope * (x_i - x_0)
            constraints.append(c_constraint)
            
        if direction is UP:
            start_beam_y = max(constraints)
        else:
            start_beam_y = min(constraints)
            
        # 4. Draw Beam
        start_pt = [x_0, start_beam_y, 0]
        end_pt = [last_pos[0], start_beam_y + slope * (last_pos[0] - x_0), 0]
        
        beam_line = Line(
            start=start_pt, 
            end=end_pt, 
            stroke_width=self.beam_thickness, 
            color=self.default_color
        )
        group.add(beam_line)
        
        # 5. Draw Stems
        for i, note_obj in enumerate(rendered_notes):
            note_pos = note_positions[i]
            notehead = note_obj[0]
            
            # Calculate beam Y at this X
            beam_y = start_beam_y + slope * (note_pos[0] - x_0)
            
            # Stem X attachment
            nh_right = notehead.get_right()[0]
            nh_left = notehead.get_left()[0]
            
            if direction is UP:
                stem_x = nh_right - 0.01
                stem_start_y = note_pos[1]
                stem_end_y = beam_y
            else:
                stem_x = nh_left + 0.01
                stem_start_y = note_pos[1]
                stem_end_y = beam_y
                
            stem = Line(
                start=[stem_x, stem_start_y, 0],
                end=[stem_x, stem_end_y, 0],
                stroke_width=self.stem_thickness,
                color=self.default_color
            )
            group.add(stem)
            
        return group

    def render_tie(self, tie: Tie, **kwargs) -> VGroup:
        """Render a Tie to a Manim VGroup."""
        group = VGroup()
        
        start_obj = self.rendered_elements_map.get(tie.start_note)
        end_obj = self.rendered_elements_map.get(tie.end_note)
        
        if not start_obj or not end_obj:
            print("Warning: Tie start or end note not found in rendered elements.")
            return group
            
        start_head = start_obj[0]
        end_head = end_obj[0]
        
        start_point = start_head.get_center()
        end_point = end_head.get_center()
        
        # Determine direction
        direction = tie.direction
        if direction == 'auto':
            avg_y = (start_point[1] + end_point[1]) / 2
            direction = DOWN if avg_y >= 0 else UP
        elif direction == 'up':
            direction = UP
        elif direction == 'down':
            direction = DOWN
            
        p0 = start_head.get_right()
        p3 = end_head.get_left()
        
        offset = 0.1 * direction
        
        p0 += offset
        p3 += offset
        
        length = np.linalg.norm(p3 - p0)
        height = length * 0.3 
        height = min(height, 0.5)
        
        p1 = p0 + direction * height + RIGHT * length * 0.25
        p2 = p3 + direction * height + LEFT * length * 0.25
        
        curve = CubicBezier(p0, p1, p2, p3, color=self.default_color, stroke_width=self.tie_thickness)
        group.add(curve)
        
        return group

    def render_rest(self, rest: Rest, **kwargs) -> VGroup:
        """Render a Rest to a Manim VGroup."""
        group = VGroup()
        
        if rest.duration >= 4.0:
            char = get_smufl_char('rest_whole')
        elif rest.duration >= 2.0:
            char = get_smufl_char('rest_half')
        elif rest.duration >= 1.0:
            char = get_smufl_char('rest_quarter')
        elif rest.duration >= 0.5:
            char = get_smufl_char('rest_eighth')
        elif rest.duration >= 0.25:
            char = get_smufl_char('rest_sixteenth')
        else:
            char = get_smufl_char('rest_quarter') # Default

        rest_obj = Text(char, font="Bravura", font_size=self.font_size, color=self.default_color)
        group.add(rest_obj)
        
        # Add dot if needed
        if rest.dot:
            dot_char = "\uE4A5" # augmentationDot
            dot = Text(dot_char, font="Bravura", font_size=self.font_size, color=self.default_color)
            dot.next_to(rest_obj, RIGHT, buff=0.1)
            # Align somewhat with the rest center or slightly up
            dot.shift(UP * 0.1)
            group.add(dot)

        
        # Set color
        if hasattr(rest, 'color') and rest.color:
             group.set_color(rest.color.to_hex() if hasattr(rest.color, 'to_hex') else rest.color)
             
        return group

    def render_barline(self, barline: Barline, **kwargs) -> VGroup:
        """Render a Barline to a Manim VGroup."""
        group = VGroup()
        
        # Barline height: from top line (2) to bottom line (-2)
        # Total height = 4 * staff_line_distance
        height = 4 * self.staff_line_distance
        
        if barline.barline_type == BarlineType.SINGLE:
            line = Line(start=UP * height/2, end=DOWN * height/2, stroke_width=self.barline_thickness, color=self.default_color)
            group.add(line)
        elif barline.barline_type == BarlineType.DOUBLE:
            line1 = Line(start=UP * height/2, end=DOWN * height/2, stroke_width=self.barline_thickness, color=self.default_color)
            line2 = Line(start=UP * height/2, end=DOWN * height/2, stroke_width=self.barline_thickness, color=self.default_color)
            line1.shift(LEFT * 0.05)
            line2.shift(RIGHT * 0.05)
            group.add(line1, line2)
        elif barline.barline_type == BarlineType.FINAL:
            line1 = Line(start=UP * height/2, end=DOWN * height/2, stroke_width=self.barline_thickness, color=self.default_color)
            line2 = Line(start=UP * height/2, end=DOWN * height/2, stroke_width=self.barline_thickness * 2, color=self.default_color) # Thicker
            line1.shift(LEFT * 0.1)
            group.add(line1, line2)
        else:
            # Default to single
            line = Line(start=UP * height/2, end=DOWN * height/2, stroke_width=self.barline_thickness, color=self.default_color)
            group.add(line)
            
        return group

    def render_clef(self, clef: Clef, **kwargs) -> Text:
        """Render a Clef to a Manim Text object."""
        clef_map = {
            'treble': 'clef_g',
            'bass': 'clef_f',
            'alto': 'clef_c',
            'tenor': 'clef_c',
            'percussion': 'clef_percussion' # Need to add this to map if used
        }
        
        char_name = clef_map.get(clef.name, 'clef_g')
        char = get_smufl_char(char_name)
        
        clef_obj = Text(char, font="Bravura", font_size=self.font_size, color=self.default_color)
        
        if clef.name == 'treble':
            # Shift down so the spiral is on the G line (-1 line from center)
            clef_obj.shift(DOWN * self.staff_line_distance) 
        elif clef.name == 'bass':
            # Shift up so the dots are on the F line (+1 line from center)
            clef_obj.shift(UP * self.staff_line_distance)
        
        return clef_obj

    KEY_SIG_POSITIONS = {
        'treble': {
            'sharp': ['F5', 'C5', 'G5', 'D5', 'A4', 'E5', 'B4'],
            'flat': ['B4', 'E5', 'A4', 'D5', 'G4', 'C5', 'F4']
        },
        'bass': {
            'sharp': ['F3', 'C3', 'G3', 'D3', 'A2', 'E3', 'B2'],
            'flat': ['B2', 'E3', 'A2', 'D3', 'G2', 'C3', 'F2']
        },
        'alto': {
            'sharp': ['G4', 'D4', 'A4', 'E4', 'B3', 'F#4', 'C#4'], 
            'flat': ['Kinda complex'] 
        }
    }

    def render_key_signature(self, key_sig: KeySignature, **kwargs) -> VGroup:
        """Render a KeySignature to a Manim VGroup."""
        group = VGroup()
        accidentals = key_sig.get_accidentals()
        
        # We need the clef to know where to place accidentals
        clef = self.context.clef or TrebleClef()
        
        # Standard positions for key signatures
        clef_name = clef.name if clef.name in self.KEY_SIG_POSITIONS else 'treble'
        
        for i, (note_name, acc_type) in enumerate(accidentals):
            acc_char = get_smufl_char('accidental_' + acc_type)
            acc_obj = Text(acc_char, font="Bravura", font_size=self.font_size, color=self.default_color)
            
            # Get standard position
            pos_list = self.KEY_SIG_POSITIONS.get(clef_name, self.KEY_SIG_POSITIONS['treble']).get(acc_type, [])
            
            if i < len(pos_list):
                target_pitch = pos_list[i]
                p_name = target_pitch[0]
                p_oct = int(target_pitch[1])
                pos = clef.get_pitch_position(p_name, p_oct)
            else:
                pos = clef.get_pitch_position(note_name, 4)
            
            y_pos = pos * (self.staff_line_distance / 2)
            acc_obj.move_to(UP * y_pos)
            
            # Horizontal spacing
            acc_obj.shift(RIGHT * i * 0.3)
            
            group.add(acc_obj)
            
        return group

    def render_time_signature(self, time_sig: TimeSignature, **kwargs) -> VGroup:
        """Render a TimeSignature to a Manim VGroup."""
        group = VGroup()
        
        if time_sig.symbol == 'C':
            char = get_smufl_char('time_sig_common')
            obj = Text(char, font="Bravura", font_size=self.font_size, color=self.default_color)
            group.add(obj)
        elif time_sig.symbol == r'\time 2/2': # Cut time
            char = get_smufl_char('time_sig_cut')
            obj = Text(char, font="Bravura", font_size=self.font_size, color=self.default_color)
            group.add(obj)
        else:
            # Render numbers
            num_str = str(time_sig.numerator)
            den_str = str(time_sig.denominator)
            
            # Numerator
            for char in num_str:
                smufl_char = get_smufl_char(f'time_sig_{char}')
                obj = Text(smufl_char, font="Bravura", font_size=self.font_size, color=self.default_color)
                # Position in top half (space 1 to 3) -> Center at space 2 (pos 2)
                # Staff lines: -2, -1, 0, 1, 2.
                # Top space is between 1 and 2. Pos 1.5?
                # Standard time sig numbers are 2 spaces high usually.
                # Top number sits on center line (0) to top line (2). Center at 1.
                obj.shift(UP * self.staff_line_distance)
                group.add(obj)
                
            # Denominator
            for char in den_str:
                smufl_char = get_smufl_char(f'time_sig_{char}')
                obj = Text(smufl_char, font="Bravura", font_size=self.font_size, color=self.default_color)
                # Position in bottom half (space -1 to -3) -> Center at space -2 (pos -1)
                # Bottom number sits on bottom line (-2) to center line (0). Center at -1.
                obj.shift(DOWN * self.staff_line_distance)
                group.add(obj)
                
        return group

    def render_staff(self, staff: Staff, **kwargs) -> VGroup:
        """Render a Staff to a Manim VGroup."""
        group = VGroup()
        elements_group = VGroup()
        
        # Start cursor at 0
        cursor_x = 0.0
        padding = 0.8 # Increased padding
        
        # 1. Render Clef
        self.context.clef = staff.clef
        clef_obj = self.render_clef(staff.clef)
        # Align clef start to cursor_x
        clef_obj.move_to(ORIGIN, aligned_edge=LEFT)
        clef_obj.shift(RIGHT * cursor_x)
        elements_group.add(clef_obj)
        
        cursor_x = clef_obj.get_right()[0] + padding
        
        # 2. Render Key Signature
        if staff.key_signature:
            key_sig_obj = self.render_key_signature(staff.key_signature)
            key_sig_obj.move_to(ORIGIN, aligned_edge=LEFT)
            key_sig_obj.shift(RIGHT * cursor_x)
            elements_group.add(key_sig_obj)
            cursor_x = key_sig_obj.get_right()[0] + padding
            
        # 3. Render Time Signature
        if staff.time_signature:
            time_sig_obj = self.render_time_signature(staff.time_signature)
            time_sig_obj.move_to(ORIGIN, aligned_edge=LEFT)
            time_sig_obj.shift(RIGHT * cursor_x)
            elements_group.add(time_sig_obj)
            cursor_x = time_sig_obj.get_right()[0] + padding
            
        # 4. Render Elements (Notes, Rests, Barlines) with Time-Based Spacing
        current_beat = 0.0
        start_x = cursor_x
        
        for element in staff.elements:
            if isinstance(element, Tie):
                continue # Render ties later
                
            element_obj = self.render(element)
            
            # Calculate position based on beat
            pos_x = start_x + current_beat * self.beat_spacing
            
            # Place element
            if isinstance(element, Beam):
                # For Beam, element_obj is a group where the first note is at local x=0.
                # We want to place the first note at pos_x.
                element_obj.shift(RIGHT * pos_x)
            else:
                # For single notes, render_note returns centered at 0.
                # We want to center it at pos_x.
                element_obj.move_to([pos_x, 0, 0], coor_mask=[1, 0, 0])
            
            elements_group.add(element_obj)
            
            # Advance beat
            if hasattr(element, 'duration'):
                current_beat += element.duration
            
            if isinstance(element, Barline):
                start_x += 0.5 
        
        # 4.5 Render Ties (now that notes are placed)
        for element in staff.elements:
            if isinstance(element, Tie):
                tie_obj = self.render(element)
                elements_group.add(tie_obj)
            
        # Calculate total width required
        if len(staff.elements) > 0:
            total_width = elements_group.get_right()[0] + 0.5
        else:
            total_width = cursor_x + 1.0
            
        # 5. Draw staff lines
        lines = VGroup()
        for i in range(-2, 3):
            y = i * self.staff_line_distance
            # Create line spanning the full width
            line = Line(start=LEFT * 0.5, end=RIGHT * total_width, stroke_width=self.staff_line_thickness, color=self.default_color)
            line.shift(UP * y)
            lines.add(line)
            
        group.add(lines)
        group.add(elements_group)
        
        # Center the whole thing
        group.move_to(ORIGIN)
            
        return group

    def render_staff_group(self, staff_group: StaffGroup, **kwargs) -> VGroup:
        """Render a StaffGroup."""
        group = VGroup()
        staves_objs = []
        
        # Render each staff
        # We need to synchronize them!
        # If we render them independently with time-based spacing, they should align horizontally
        # provided they have the same beat_spacing and start_x.
        # render_staff centers the result. This destroys alignment if widths differ.
        
        # We need to render them, then align them left.
        
        max_width = 0
        
        for i, staff in enumerate(staff_group.staves):
            staff_obj = self.render_staff(staff)
            # Shift down
            staff_obj.shift(DOWN * i * 3.0) # 3.0 units between staves
            
            # Align left to 0 for now
            staff_obj.move_to(ORIGIN, aligned_edge=LEFT)
            staff_obj.shift(DOWN * i * 3.0) # Re-apply Y shift
            
            group.add(staff_obj)
            staves_objs.append(staff_obj)
            
            if staff_obj.width > max_width:
                max_width = staff_obj.width
                
        # Add connecting line at start (System Start Line)
        if len(staves_objs) > 1:
            top_staff = staves_objs[0]
            bottom_staff = staves_objs[-1]
            
            # Top of top staff lines: top staff center Y + 2 * dist
            # Bottom of bottom staff lines: bottom staff center Y - 2 * dist
            # Note: staff_obj center Y might be different from staff lines center Y if elements go high/low.
            # But render_staff centers the whole group.
            # We need the Y of the lines.
            # The lines are the first element in the group (index 0).
            
            top_lines = staves_objs[0][0]
            bottom_lines = staves_objs[-1][0]
            
            top_y = top_lines.get_top()[1]
            bottom_y = bottom_lines.get_bottom()[1]
            
            # X position: start of lines.
            # Lines start at LEFT * 0.5 relative to staff_obj origin?
            # render_staff: line starts at LEFT * 0.5 relative to uncentered group.
            # Then group is centered.
            # Then we moved staff_obj to align LEFT at ORIGIN.
            # So staff_obj.get_left()[0] is 0.
            # The lines start at... let's check render_staff.
            # line start = -0.5.
            # group.move_to(ORIGIN).
            # So left edge is determined by bounding box.
            # If we align staff_obj left to 0.
            # The lines should be at roughly the same X if padding is consistent.
            
            # Let's use the left edge of the top staff lines.
            x_pos = top_lines.get_left()[0]
            
            # System Start Line
            connector = Line(start=[x_pos, top_y, 0], end=[x_pos, bottom_y, 0], stroke_width=self.barline_thickness, color=self.default_color)
            group.add(connector)
            
            # Add Brace
            # SMuFL brace is 'brace'.
            brace_char = get_smufl_char('brace')
            brace = Text(brace_char, font="Bravura", font_size=self.font_size * 2.5, color=self.default_color) # Scale up
            # Position brace to the left of the connector
            brace.next_to(connector, LEFT, buff=0.2)
            # Stretch brace vertically to match height?
            # Text objects can be scaled.
            target_height = top_y - bottom_y + 0.5 # A bit extra
            # brace.height = target_height # This might distort it weirdly if aspect ratio is locked?
            # Manim Text allows scaling.
            brace.scale_to_fit_height(target_height)
            group.add(brace)
            
        # Center the whole group
        group.move_to(ORIGIN)
            
        return group
