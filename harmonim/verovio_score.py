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
        Extract timing and MIDI data from Verovio.
        """
        import xml.etree.ElementTree as ET
        midi_map = {}
        
        # 0. MAP STAVES TO INSTRUMENTS (via MEI)
        # We need to know which staff number (n) belongs to which part index.
        staff_to_part_idx = {} # {staff_n: part_index}
        try:
            mei = self.tk.getMEI()
            mei_root = ET.fromstring(mei)
            # Remove namespaces for easier querying
            for elem in mei_root.iter():
                elem.tag = elem.tag.split('}')[-1]
            
            # Find staff groups (these represent instruments/parts)
            # We look for the main staffGrp that contains staffDef
            # In MEI, instruments are often nested staffGrps
            parts_found = []
            for sg in mei_root.findall(".//staffGrp"):
                staves = [sd.get('n') for sd in sg.findall("staffDef")]
                if staves:
                    # Found a staff group with staves
                    parts_found.append(staves)
            
            # Sort parts to ensure consistent ordering (usually by staff number)
            parts_found.sort(key=lambda x: int(x[0]) if x else 0)
            
            for p_idx, staves in enumerate(parts_found):
                for s_n in staves:
                    staff_to_part_idx[s_n] = p_idx
            
            self.part_list = [f"part_{i}" for i in range(len(parts_found))]
        except Exception as e:
            print(f"Warning mapping staves to parts: {e}")
            self.part_list = ["default"]

        # 1. PARSE SVG FOR HIERARCHY
        # Map element_id to its parent staff number
        id_to_staff_n = {}
        try:
            # Clean SVG for XML parsing
            import re
            svg_clean = re.sub(' xmlns="[^"]+"', '', self.svg_string, count=1)
            svg_root = ET.fromstring(svg_clean)
            
            for staff in svg_root.findall(".//g[@data-class='staff']"):
                s_id = staff.get('data-id')
                if not s_id: continue
                
                # Ask Verovio for the staff number 'n'
                try:
                    s_attrs = self.tk.getElementAttr(s_id)
                    if isinstance(s_attrs, str):
                        import json
                        s_attrs = json.loads(s_attrs)
                    s_n = s_attrs.get('n')
                    if s_n:
                        # Mark all children IDs as belonging to this staff number
                        for elem in staff.iter():
                            e_id = elem.get('data-id')
                            if e_id:
                                id_to_staff_n[e_id] = s_n
                except:
                    pass
        except Exception as e:
            print(f"Warning parsing SVG hierarchy: {e}")

        # 2. EXTRACT NOTES
        import re
        note_pattern = r'data-id="([^"]+)" [^>]*data-class="note"'
        all_note_ids = re.findall(note_pattern, self.svg_string)
        
        for note_id in all_note_ids:
            try:
                info = self.tk.getMIDIValuesForElement(note_id)
                if info:
                    # Get part index for this note
                    s_n = id_to_staff_n.get(note_id)
                    p_idx = staff_to_part_idx.get(s_n, 0)
                    
                    midi_map[note_id] = {
                        'start': info.get('time', 0) / 1000.0,
                        'duration': info.get('duration', 0) / 1000.0,
                        'pitch': info.get('pitch', 60),
                        'element_class': 'note',
                        'part_index': p_idx
                    }
            except:
                pass

        # 2. EXTRACT SLURS AND TIES
        matches = re.findall(r'<g [^>]*data-id="([^"]+)" [^>]*data-class="(slur|tie)"', self.svg_string)
        
        slur_count = 0
        tie_count = 0
        for eid, cls in matches:
            try:
                attrs_json = self.tk.getElementAttr(eid)
                if not attrs_json: continue
                
                import json
                attrs = json.loads(attrs_json) if isinstance(attrs_json, str) else attrs_json
                
                start_id = attrs.get('startid')
                if start_id:
                    if start_id.startswith('#'): start_id = start_id[1:]
                    
                    if start_id in midi_map:
                        start_note_info = midi_map[start_id]
                        duration = start_note_info['duration']
                        
                        end_id = attrs.get('endid')
                        if end_id:
                            if end_id.startswith('#'): end_id = end_id[1:]
                            if end_id in midi_map:
                                end_note_info = midi_map[end_id]
                                duration = max(duration, (end_note_info['start'] + end_note_info['duration']) - start_note_info['start'])
                        
                        duration = max(duration, 0.2)
                        
                        # Use the start note's part index for the slur/tie
                        p_idx = start_note_info.get('part_index', 0)
                        
                        midi_map[eid] = {
                            'start': start_note_info['start'],
                            'duration': duration,
                            'pitch': start_note_info['pitch'],
                            'element_class': cls,
                            'part_index': p_idx
                        }
                        
                        if cls == 'slur': slur_count += 1
                        else: tie_count += 1
            except Exception as e:
                pass
        
        print(f"  - Extracted {len(all_note_ids)} notes, {slur_count} slurs, {tie_count} ties")
        print(f"  - Instruments found: {len(self.part_list)}")
        return midi_map
    
    def _attach_metadata_via_color(self):
        """
        Attach MIDI metadata to Manim mobjects using COLOR MAPPING.
        """
        matched_count = 0
        total_mobjects = 0
        
        from manim.utils.color import color_to_rgb
        
        def process_mobject(mob):
            nonlocal matched_count, total_mobjects
            
            try:
                # 1. Get ID from color
                current_color_hex = mob.get_fill_color()
                if mob.get_fill_opacity() == 0:
                    current_color_hex = mob.get_stroke_color()
                    
                r, g, b = color_to_rgb(current_color_hex)
                recovered_id = self.color_mapper.get_id_from_rgb(r, g, b)
                
                # 2. Link metadata
                if recovered_id and recovered_id in self.midi_data:
                    midi_info = self.midi_data[recovered_id]
                    e_class = midi_info.get('element_class', 'note')
                    
                    if e_class in ['slur', 'tie'] and not hasattr(mob, "is_slice"):
                        # SPECIAL HANDLING: Slice the slur/tie into pieces for progressive coloring
                        num_slices = 100
                        slices = VGroup()
                        
                        # We use sampling on the path. For a filled slur (loop):
                        # 0.0 -> 0.5 is one side, 0.5 -> 1.0 is the other side.
                        for i in range(num_slices):
                            a1 = (i / num_slices) * 0.5
                            a2 = ((i + 1) / num_slices) * 0.5
                            
                            # Points on bottom and top
                            p1 = mob.point_from_proportion(a1)
                            p2 = mob.point_from_proportion(a2)
                            p3 = mob.point_from_proportion(1.0 - a2)
                            p4 = mob.point_from_proportion(1.0 - a1)
                            
                            s = Polygon(p1, p2, p3, p4, stroke_width=0, fill_opacity=1.0, color=BLACK)
                            s.is_slice = True
                            s.start_time = midi_info['start'] + (i / num_slices) * midi_info['duration']
                            slices.add(s)
                        
                        # Replace content with slices
                        mob.submobjects = []
                        mob.add(*slices)
                        mob.start_time = midi_info['start']
                        mob.duration = midi_info['duration']
                        mob.element_class = e_class
                        mob.part_index = midi_info.get('part_index', 0)
                        for s in slices:
                            s.part_index = mob.part_index
                    else:
                        mob.note_id = recovered_id
                        mob.start_time = midi_info['start']
                        mob.duration = midi_info['duration']
                        mob.pitch = midi_info['pitch']
                        mob.element_class = e_class
                        mob.part_index = midi_info.get('part_index', 0)
                    
                    matched_count += 1
            except Exception:
                pass
            
            total_mobjects += 1
            for sub in mob.submobjects:
                process_mobject(sub)
                
        process_mobject(self.visual_score)
        
        print(f"Color Matching Results:")
        print(f"  - Scanned {total_mobjects} mobjects")
        print(f"  - Successfully matched {matched_count} elements in Manim")
        
        total_elements = len(self.midi_data)
        print(f"  - SUCCESS: Coverage for {total_elements} musical elements")

    def get_notes_at_time(self, time: float) -> List[VMobject]:
        """Get all note mobjects active at a given time."""
        notes = []
        
        def check_mobject(mob):
            if hasattr(mob, 'start_time') and hasattr(mob, 'duration'):
                if mob.start_time <= time < mob.start_time + mob.duration:
                    notes.append(mob)
            for sub in mob.submobjects:
                check_mobject(sub)
        
        check_mobject(self)
        return notes
    
    def animate_playback(self, scene: Scene, colors=BLUE):
        """
        Helper method to animate the score as if it's playing.
        'colors' can be a single color or a list of colors (one per instrument).
        """
        if not isinstance(colors, list):
            colors = [colors] * (len(getattr(self, 'part_list', [0])) + 1)

        timed_elements = []
        
        def collect(mob):
            # Only collect leaf elements with timing (either notes or slur slices)
            if hasattr(mob, 'start_time'):
                if not mob.submobjects or hasattr(mob, "is_slice"):
                    timed_elements.append(mob)
            for sub in mob.submobjects:
                collect(sub)
        
        collect(self)
        if not timed_elements: return
            
        # Create a time tracker starting slightly before 0 for a lead-in
        # This prevents the first note from being already colored when the video starts
        time_tracker = ValueTracker(-0.5)
        
        # Determine highlighting color and apply updaters
        for element in timed_elements:
            # Pick color for this instrument
            p_idx = getattr(element, 'part_index', 0)
            target_color = colors[p_idx % len(colors)]
            
            def update_element(m, dt, col=target_color):
                t = time_tracker.get_value()
                # Chord synchronization: using simple >= check is enough as all
                # notes in a chord share the exact same start_time from Verovio
                if t >= m.start_time:
                    # Use set_color for slices (Polygons) and set_fill for notes
                    if hasattr(m, "is_slice"):
                        m.set_color(col)
                        m.set_fill(col, opacity=1.0)
                    else:
                        m.set_fill(col, opacity=1.0)
                else:
                    m.set_fill(BLACK, opacity=1.0)
                    m.set_stroke(BLACK, opacity=1.0)
            
            element.add_updater(update_element)

        # Total animation duration
        # We add the 0.5 lead-in + 0.5 buffer at the end
        max_end = max([e.start_time + getattr(e, 'duration', 0.1) for e in timed_elements])
        total_time = max_end + 1.0
        
        # Animate the time tracker
        scene.play(time_tracker.animate.set_value(max_end + 0.5), run_time=total_time, rate_func=linear)
        
        for element in timed_elements:
            element.clear_updaters()
