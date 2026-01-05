"""
VerovioScore - A VGroup that intelligently maps MIDI data to Manim mobjects.

This class solves the ID mapping problem by:
1. Rendering SVG with Verovio
2. Extracting timing/MIDI data from Verovio
3. Injecting unique colors into the SVG to encode element IDs
4. Loading the SVG in Manim (colors are preserved)
5. Decoded colors back to IDs to attach metadata
6. Restoring original visual styling
"""
from manim import *
import verovio
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from harmonim.renderers.verovio_color_mapper import ColorIDMapper, inject_colors_to_svg


class VerovioScore(VGroup):
    """
    A musical score that knows its own timing.
    
    Each note mobject has attributes:
    - note_id: Verovio's ID for this element
    - start_time: When this note starts (seconds)
    - duration: How long it lasts (seconds)  
    - pitch: MIDI pitch number
    """
    
    def __init__(self, musicxml_path: str, **kwargs):
        super().__init__(**kwargs)
        self.musicxml_path = str(musicxml_path)
        
        # 1. Initialize Verovio
        self.tk = verovio.toolkit()
        self.tk.setOptions({
            "scale": 50,
            "adjustPageHeight": True,
            "font": "Bravura",
            "svgViewBox": True,
            "svgHtml5": True,  # Preserves data-id
            "header": "none",
            "footer": "none"
        })
        
        if not self.tk.loadFile(self.musicxml_path):
            raise ValueError(f"Could not load {musicxml_path}")
        
        # 2. Generate SVG
        self.svg_string = self.tk.renderToSVG(1)
        
        # 3. Extract MIDI/timing data from Verovio
        self.midi_data = self._extract_midi_data()
        
        print(f"MIDI data extracted for {len(self.midi_data)} elements")
        
        # 4. COLOR INJECTION FOR ID MAPPING
        # We need to create a map of ID -> Color and inject it into the SVG
        self.color_mapper = ColorIDMapper()
        
        # Only care about elements we have MIDI data for
        ids_to_map = list(self.midi_data.keys())
        
        # Inject colors!
        colored_svg = inject_colors_to_svg(self.svg_string, ids_to_map, self.color_mapper)
        
        # 5. Load visual in Manim
        temp_path = Path("output") / "temp_verovio_score.svg"
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(colored_svg)
        
        # Load SVG into Manim - Manim will parse the colors we injected
        self.visual_score = SVGMobject(str(temp_path))
        
        # 6. THE MAGIC LINKING (via Color)
        self._attach_metadata_via_color()
        
        # 7. Add to this VGroup
        self.add(self.visual_score)
        
        # 8. Restore visual appearance
        # Reset everything to black (or user preference)
        # This overwrites the "hack" colors
        self.set_color(BLACK)
    
    def _extract_midi_data(self) -> Dict:
        """
        Extract MIDI timing data from Verovio.
        
        Returns dict: {note_id: {start: ms, duration: ms, pitch: int}}
        """
        midi_map = {}
        
        # Use Verovio's timing API
        timemap = self.tk.renderToTimemap()
        
        # Build a set of all note IDs from timemap
        all_note_ids = set()
        for event in timemap:
            all_note_ids.update(event.get('on', []))
        
        # Get MIDI info for each note
        for note_id in all_note_ids:
            try:
                info = self.tk.getMIDIValuesForElement(note_id)
                if info:
                    midi_map[note_id] = {
                        'start': info.get('time', 0) / 1000.0,  # Convert to seconds
                        'duration': info.get('duration', 0) / 1000.0,
                        'pitch': info.get('pitch', 60)
                    }
            except:
                pass
        
        return midi_map
    
    def _attach_metadata_via_color(self):
        """
        Attach MIDI metadata to Manim mobjects using COLOR MAPPING.
        
        Strategy:
        1. Iterate through every sub-mobject loaded by Manim.
        2. Check its fill/stroke color.
        3. Convert color -> ID using ColorIDMapper.
        4. If ID matches, attach metadata.
        """
        matched_count = 0
        total_mobjects = 0
        
        # Helper to traverse all mobjects (Manim SVG structure can be nested)
        def process_mobject(mob):
            nonlocal matched_count, total_mobjects
            
            # If it's a "leaf" mobject (has points but no submobjects, or is a path)
            # Manim SVGMobject structure: usually VGroups of VMobjects.
            # We check color on everything.
            
            # Check fill color
            # Manim stores colors as Hex or RGBA. We need to be careful.
            # get_fill_color() usually returns hex string or Color object.
            # get_color() returns the main color.
            
            # Note: SVGMobject usually sets fill_color and stroke_color
            
            try:
                # Get color as RGB tuple (0-1 range)
                # We prioritize fill, then stroke
                fill_rgba = mob.get_fill_color() 
                # Manim color might be a Color object or string. 
                # safe way: mob.fill_color which is ManimColor (internal)
                # But mob.get_fill_color() returns a string (hex) usually?
                # Actually, recently Manim changed colors. Let's use get_color() if unsure.
                
                # We'll rely on the color mapper to handle RGB floats if we can get them.
                # VMobject.get_fill_color() -> ManimColor or str
                
                # Let's try to get hex to be safe, or rgb components.
                # In Manim Community 0.18+, colors are objects.
                
                from manim.utils.color import color_to_rgb
                
                current_color_hex = mob.get_fill_color()
                # If transparent/no fill, try stroke
                if mob.get_fill_opacity() == 0:
                    current_color_hex = mob.get_stroke_color()
                    
                r, g, b = color_to_rgb(current_color_hex)
                
                # Recover ID
                recovered_id = self.color_mapper.get_id_from_rgb(r, g, b)
                
                if recovered_id and recovered_id in self.midi_data:
                    # MATCH FOUND!
                    midi_info = self.midi_data[recovered_id]
                    
                    mob.note_id = recovered_id
                    mob.start_time = midi_info['start']
                    mob.duration = midi_info['duration']
                    mob.pitch = midi_info['pitch']
                    
                    matched_count += 1
                    
            except Exception as e:
                # Color match failed or invalid color type
                pass
            
            total_mobjects += 1
            
            # Recurse
            for sub in mob.submobjects:
                process_mobject(sub)
                
        # Start traversal
        process_mobject(self.visual_score)
        
        print(f"Color Matching Results:")
        print(f"  - Scanned {total_mobjects} mobjects")
        print(f"  - Successfully matched {matched_count} notes")
        
        # Check coverage
        total_notes = len(self.midi_data)
        if matched_count < total_notes:
            print(f"  - WARNING: Missed {total_notes - matched_count} notes!")
        else:
            print(f"  - SUCCESS: 100% Matching ({matched_count}/{total_notes})")

    def get_notes_at_time(self, time: float) -> List[VMobject]:
        """Get all note mobjects active at a given time."""
        notes = []
        
        def check_mobject(mob):
            if hasattr(mob, 'start_time') and hasattr(mob, 'duration'):
                # Simple logic for now: exact overlap
                # In practice, strict equality might miss slightly offset events
                if mob.start_time <= time < mob.start_time + mob.duration:
                    notes.append(mob)
            for sub in mob.submobjects:
                check_mobject(sub)
        
        check_mobject(self)
        return notes
    
    def animate_playback(self, scene: Scene, color=BLUE):
        """
        Helper method to animate the score as if it's playing.
        """
        # Collect all notes with timing
        timed_notes = []
        
        def collect(mob):
            if hasattr(mob, 'start_time'):
                timed_notes.append(mob)
            for sub in mob.submobjects:
                collect(sub)
        
        collect(self)
        
        # Sort by start time
        timed_notes.sort(key=lambda m: m.start_time)
        
        if not timed_notes:
            print("No timed notes found!")
            return
        
        # Group by start time
        from collections import defaultdict
        time_groups = defaultdict(list)
        for note in timed_notes:
            time_groups[note.start_time].append(note)
        
        # Animate
        last_time = 0.0
        for start_time in sorted(time_groups.keys()):
            # Wait until this time
            wait_duration = start_time - last_time
            if wait_duration > 0:
                scene.wait(wait_duration)
            
            # Color all notes starting now
            notes = time_groups[start_time]
            anims = [note.animate.set_fill(color, opacity=1.0) for note in notes]
            
            if anims:
                scene.play(AnimationGroup(*anims, lag_ratio=0), run_time=0.1)
            
            last_time = start_time
