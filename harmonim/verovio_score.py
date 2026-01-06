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
            "noText": 1,       # Converts dynamic marks to paths
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
        import re
        import json
        midi_map = {}
        
        # 0. MAP STAVES TO INSTRUMENTS (via MEI)
        # We need to know which staff number (n) belongs to which part index (P1, P2...).
        staff_to_part_idx = {} # {staff_n: part_index}
        try:
            # 1. Get MEI and STRIP NAMESPACES for total reliability
            mei = self.tk.getMEI()
            # Remove all xmlns="..." and prefixes like mei: or xml:
            mei_clean = re.sub(r' xmlns(:[a-z]+)?="[^"]+"', '', mei)
            mei_clean = re.sub(r'([a-z]+):id=', r'id=', mei_clean)
            
            mei_root = ET.fromstring(mei_clean)
            
            # Find all parts
            # We look for staffDef or staffGrp that have an id starting with 'P'
            parts_found = {} # {part_id: [staff_n]}
            
            for elem in mei_root.iter():
                eid = elem.get('id')
                if eid and eid.startswith('P') and len(eid) < 8:
                    if elem.tag == 'staffDef':
                        s_n = elem.get('n')
                        if s_n: parts_found[eid] = [s_n]
                    elif elem.tag == 'staffGrp':
                        staves = [sd.get('n') for sd in elem.findall(".//staffDef")]
                        if staves: parts_found[eid] = staves
            
            # If nothing found with 'P', fallback to all individual staves as parts
            if not parts_found:
                for sd in mei_root.findall(".//staffDef"):
                    s_n = sd.get('n')
                    if s_n: parts_found[f"S{s_n}"] = [s_n]

            # Natural sort by part number (P1, P2...)
            sorted_part_ids = sorted(parts_found.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
            
            for p_idx, p_id in enumerate(sorted_part_ids):
                for s_n in parts_found[p_id]:
                    staff_to_part_idx[s_n] = p_idx
            
            self.part_list = sorted_part_ids
        except Exception as e:
            print(f"Warning mapping staves to parts: {e}")
            self.part_list = ["default"]

        # 1. PARSE SVG FOR HIERARCHY
        # Map element_id to its parent staff number
        id_to_staff_n = {}
        try:
            # Clean SVG namespaces
            svg_clean = re.sub(' xmlns="[^"]+"', '', self.svg_string, count=1)
            svg_root = ET.fromstring(svg_clean)
            
            for staff in svg_root.findall(".//g[@data-class='staff']"):
                s_id = staff.get('data-id')
                if not s_id: continue
                
                # Get staff number 'n'
                try:
                    s_attrs = self.tk.getElementAttr(s_id)
                    if isinstance(s_attrs, str):
                        s_attrs = json.loads(s_attrs)
                    s_n = s_attrs.get('n')
                    
                    if s_n:
                        # Mark all children (notes, etc) as belonging to this staff n
                        for elem in staff.iter():
                            e_id = elem.get('data-id')
                            if e_id:
                                id_to_staff_n[e_id] = s_n
                except: pass
        except Exception as e:
            print(f"Warning parsing SVG hierarchy: {e}")

        # 2. EXTRACT NOTES
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
                        'part_index': p_idx,
                        'staff_n': s_n
                    }
            except:
                pass

        # 3. SPATIAL TIME MAPPING (For dynamics/hairpins)
        # staff_n -> list of (x_coord, time)
        staff_time_map = {}
        for eid, info in midi_map.items():
            if info['element_class'] == 'note':
                s_n = id_to_staff_n.get(eid)
                if s_n not in staff_time_map: staff_time_map[s_n] = []
                # We'll fill x_coord during metadata attachment
        
        # 4. EXTRACT SLURS AND TIES (Keep as is, they use startid)
        # ... (rest of old code)
        matches = re.findall(r'<g [^>]*data-id="([^"]+)" [^>]*data-class="(slur|tie)"', self.svg_string)
        
        slur_count = 0
        tie_count = 0
        for eid, cls in matches:
            try:
                attrs = self.tk.getElementAttr(eid)
                if not attrs: continue
                if isinstance(attrs, str): attrs = json.loads(attrs)
                
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
            except Exception: pass

        # 5. EXTRACT DYNAMICS (Timing will be resolved spatially in Manim)
        dyn_matches = re.findall(r'<g [^>]*data-id="([^"]+)" [^>]*data-class="(hairpin|dynam)"', self.svg_string)
        dyn_count = 0
        hairpin_count = 0
        
        for eid, cls in dyn_matches:
            try:
                attrs = self.tk.getElementAttr(eid)
                if not attrs: continue
                if isinstance(attrs, str): attrs = json.loads(attrs)
                
                s_n = attrs.get('staff', '1')
                p_idx = staff_to_part_idx.get(s_n, 0)
                
                midi_map[eid] = {
                    'start': 0, # Placeholder
                    'duration': 0.5,
                    'element_class': cls,
                    'part_index': p_idx,
                    'staff_n': s_n,
                    'needs_spatial_timing': True
                }
                if cls == 'hairpin': hairpin_count += 1
                else: dyn_count += 1
            except Exception: pass
        
        # 6. EXTRACT ARTICULATIONS
        # Parse MEI to map Articulations -> Parent Notes
        artic_to_note = {} # artic_id -> note_id
        try:
            for note in mei_root.findall(".//note"):
                note_id = note.get('id')
                if not note_id: continue
                for child in note:
                    child_id = child.get('id')
                    if child_id: artic_to_note[child_id] = note_id
        except: pass

        # Find articulations in SVG
        # Note: SVG might use 'artic technical' so we match data-class="artic" or similar
        artic_matches = re.findall(r'<g [^>]*data-id="([^"]+)" [^>]*data-class="([^"]+)"', self.svg_string)
        # Filter for classes containing 'artic'
        artic_ids = [eid for eid, cls in artic_matches if 'artic' in cls]
        
        artic_count = 0
        for aid in artic_ids:
            # Find parent note from MEI map
            parent_note_id = artic_to_note.get(aid)
            if parent_note_id and parent_note_id in midi_map:
                p_info = midi_map[parent_note_id]
                midi_map[aid] = {
                    'start': p_info['start'],
                    'duration': p_info['duration'],
                    # 'pitch': p_info['pitch'], # Not needed
                    'element_class': 'articulation',
                    'part_index': p_info.get('part_index', 0),
                    'staff_n': p_info.get('staff_n', '1')
                }
                artic_count += 1
        
        print(f"  - Extracted {len(all_note_ids)} notes, {slur_count} slurs, {tie_count} ties")
        print(f"  - Extracted {dyn_count} dynamic marks, {hairpin_count} hairpins")
        print(f"  - Extracted {artic_count} articulations")
        return midi_map
    
    def _attach_metadata_via_color(self):
        """
        Attach MIDI metadata to Manim mobjects using COLOR MAPPING.
        Supports spatial timing for dynamics/hairpins.
        """
        matched_count = 0
        
        # staff_n -> list of (x_coord, time)
        staff_anchors = {} 
        
        # 1. PASS ONE: FIND NOTES AND COLLECT ANCHORS
        all_matched = [] # List of (mobject, recovered_id)
        
        def first_pass(mob):
            recovered_id = None
            if isinstance(mob, VMobject):
                try:
                    fill = mob.get_fill_color()
                    if fill:
                         r, g, b = fill.to_rgb()
                    else:
                        raise ValueError()

                    if mob.get_fill_opacity() == 0:
                        stroke = mob.get_stroke_color()
                        if stroke:
                            r, g, b = stroke.to_rgb()
                        else:
                            raise ValueError()
                    
                    recovered_id = self.color_mapper.get_id_from_rgb(r, g, b)
                except:
                    pass
                
            if recovered_id and recovered_id in self.midi_data:
                midi_info = self.midi_data[recovered_id]
                all_matched.append((mob, recovered_id))
                
                if midi_info.get('element_class') == 'note':
                    s_n = midi_info.get('staff_n', '1')
                    if s_n not in staff_anchors: staff_anchors[s_n] = []
                    staff_anchors[s_n].append((mob.get_center()[0], midi_info['start']))
            
            for sub in mob.submobjects:
                first_pass(sub)

        first_pass(self.visual_score)
        
        # Sort anchors by X
        for s in staff_anchors:
            staff_anchors[s].sort()

        # 2. PASS TWO: RESOLVE TIMING AND ATTACH
        for mob, recovered_id in all_matched:
            midi_info = self.midi_data[recovered_id]
            e_class = midi_info.get('element_class', 'note')
            
            # Resolve spatial timing if needed
            if midi_info.get('needs_spatial_timing'):
                s_n = midi_info.get('staff_n', '1')
                anchors = staff_anchors.get(s_n, [])
                if not anchors: # fallback to all anchors
                    anchors = [a for s in staff_anchors.values() for a in s]
                    anchors.sort()
                
                if anchors:
                    # Find nearest time for start (left side)
                    x_start = mob.get_left()[0]
                    closest_start = min(anchors, key=lambda a: abs(a[0] - x_start))
                    midi_info['start'] = closest_start[1]
                    
                    if e_class == 'hairpin':
                        # Find nearest time for end (right side)
                        x_end = mob.get_right()[0]
                        closest_end = min(anchors, key=lambda a: abs(a[0] - x_end))
                        midi_info['duration'] = max(0.1, closest_end[1] - midi_info['start'])
                    else:
                        midi_info['duration'] = 0.5

            # Apply metadata
            # Apply metadata
            # Apply metadata
            if e_class in ['slur', 'tie', 'hairpin'] and not hasattr(mob, "is_slice"):
                num_slices = 100
                slices = VGroup()
                
                if e_class == 'hairpin':
                    # LINEAR SLICING for hairpins (wedge shape)
                    # Generate separate lines for top and bottom to avoid filling
                    stroke_w = mob.get_stroke_width()
                    if stroke_w < 0.5: stroke_w = 3.0 
                    
                    # Generate raw segments first without worrying about order
                    raw_segments = []
                    for i in range(num_slices):
                        try:
                            a1 = i / num_slices
                            a2 = (i + 1) / num_slices
                            
                            # Naive mapping 0-0.5 top, 1.0-0.5 bottom assumption
                            # We just grab segments from both "sides" of the proportion loop
                            p1 = mob.point_from_proportion(a1 * 0.5)
                            p2 = mob.point_from_proportion(a2 * 0.5)
                            
                            p3 = mob.point_from_proportion(1.0 - (a1 * 0.5))
                            p4 = mob.point_from_proportion(1.0 - (a2 * 0.5))
                            
                            l1 = Line(p1, p2, stroke_width=stroke_w, color=BLACK)
                            l2 = Line(p3, p4, stroke_width=stroke_w, color=BLACK)
                            raw_segments.extend([l1, l2])
                        except: pass
                    
                    # SORT BY X to ensure time flows Left -> Right
                    raw_segments.sort(key=lambda m: m.get_center()[0])
                    for i, s in enumerate(raw_segments):
                        s.is_slice = True
                        # Map i to time range strictly L->R
                        alpha = i / len(raw_segments)
                        s.start_time = midi_info['start'] + alpha * midi_info['duration']
                        s.part_index = midi_info.get('part_index', 0)
                        slices.add(s)

                else:
                    # LOOP SLICING for Slurs/Ties (Filled Polygon slices)
                    raw_polys = []
                    for i in range(num_slices):
                        try:
                            a1 = (i / num_slices) * 0.5
                            a2 = ((i + 1) / num_slices) * 0.5
                            p1 = mob.point_from_proportion(a1)
                            p2 = mob.point_from_proportion(a2)
                            p3 = mob.point_from_proportion(1.0 - a2)
                            p4 = mob.point_from_proportion(1.0 - a1)
                            s = Polygon(p1, p2, p3, p4, stroke_width=0, fill_opacity=1.0, color=BLACK)
                            raw_polys.append(s)
                        except: pass
                    
                    # Sort slurs L->R as well? Usually strictly correlated.
                    # Some slurs arc back? No, usually timing is X-axis based in standard notation.
                    raw_polys.sort(key=lambda m: m.get_center()[0])
                    for i, s in enumerate(raw_polys):
                        s.is_slice = True
                        alpha = i / len(raw_polys)
                        s.start_time = midi_info['start'] + alpha * midi_info['duration']
                        s.part_index = midi_info.get('part_index', 0)
                        slices.add(s)
                
                # CRITICAL: CLEAR PARENT GEOMETRY so it doesn't show the unfilled/black shape underneath
                mob.points = np.zeros((0, 3))
                mob.set_fill(opacity=0)
                mob.set_stroke(opacity=0)
                
                mob.submobjects = []
                mob.add(*slices)
                mob.start_time = midi_info['start']
                mob.duration = midi_info['duration']
                mob.element_class = e_class
                mob.part_index = midi_info.get('part_index', 0)
            else:
                mob.note_id = recovered_id
                mob.start_time = midi_info['start']
                mob.duration = midi_info['duration']
                mob.element_class = e_class
                mob.part_index = midi_info.get('part_index', 0)
            
            matched_count += 1
        
        print(f"Color Matching Results:")
        print(f"  - Successfully matched {matched_count} elements in Manim")

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
                        m.set_stroke(col, opacity=1.0)
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
