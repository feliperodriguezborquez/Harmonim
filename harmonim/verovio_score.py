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
        self.scrolling = kwargs.pop("scrolling", False)
        super().__init__(**kwargs)
        self.musicxml_path = str(musicxml_path)
        
        # 1. Initialize Verovio
        self.tk = verovio.toolkit()
        
        options = {
            "scale": 50,
            "adjustPageHeight": True,
            "font": "Bravura",
            "svgViewBox": True,
            "svgHtml5": True,  # Preserves data-id
            "noText": 1,       # Converts dynamic marks to paths
            "header": "none",
            "footer": "none"
        }
        
        if self.scrolling:
            # Create a single huge page for infinite scrolling
            options.update({
                "pageWidth": 60000, 
                "breaks": "none",
                "spacingNonLinear": 0.0  # Force proportional spacing for constant speed
            })
            
        self.tk.setOptions(options)
        
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
        
        if self.scrolling:
            # Huge width causes auto-scaling to make it tiny. 
            # We must restore a reasonable height.
            self.visual_score.scale_to_fit_height(6)
        
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

        # 4.5. RESOLVE RESTS VIA MEI SEQUENCING
        # Build timeline per layer to solve Rest timing accurately
        dur_map = {'long': 16, 'breve': 8, '1': 4, '2': 2, '4': 1, '8': 0.5, '16': 0.25, '32': 0.125, '64': 0.0625}
        
        def get_ppq(el):
            d = el.get('dur')
            val = dur_map.get(d, 0)
            if el.get('dots') == '1': val *= 1.5
            return val

        try:
            def get_id(node):
                return node.get('{http://www.w3.org/XML/1998/namespace}id') or node.get('id')
            
            # Collect elements across the entire score into continuous streams per (Staff, Layer)
            streams = {} # (staff_n, layer_n) -> [elements]

            for measure in mei_root.findall(".//measure"):
                for staff in measure.findall(".//staff"):
                    s_n = staff.get('n', '1')
                    for layer in staff.findall(".//layer"):
                        l_n = layer.get('n', '1')
                        key = (s_n, l_n)
                        if key not in streams: streams[key] = []
                        
                        # Flatten layer elements
                        layer_elems = []
                        def flatten(node):
                            tag = node.tag.split('}')[-1]
                            if tag in ['note', 'rest', 'chord', 'beam', 'mRest']:
                                if tag == 'beam': 
                                    for child in node: flatten(child)
                                elif tag == 'chord':
                                    f_note = node.find(".//note") 
                                    if f_note is None: 
                                         for child in node:
                                             if 'note' in child.tag: 
                                                 f_note = child; break
                                    if f_note is not None: layer_elems.append(f_note)
                                else:
                                    layer_elems.append(node)
                        
                        for item in layer: flatten(item)
                        streams[key].extend(layer_elems)

            # Process each stream independently
            for key, elements in streams.items():
                s_n = key[0]
                
                sync_indices = []
                for i, el in enumerate(elements):
                    eid = get_id(el)
                    if eid and eid in midi_map: sync_indices.append(i)
                
                def add_rest_to_map(el, t_start, t_dur, ref_info):
                    eid_gap = get_id(el)
                    tag = el.tag.split('}')[-1]
                    if tag in ['rest', 'mRest'] and eid_gap:
                        midi_map[eid_gap] = {
                            'start': t_start,
                            'duration': t_dur,
                            'element_class': 'rest',
                            'part_index': ref_info.get('part_index', 0),
                            'staff_n': s_n
                        }

                if sync_indices:
                     # Calculate PPQ Factor from first sync note
                     idx0 = sync_indices[0]
                     node0 = elements[idx0]
                     info0 = midi_map.get(get_id(node0))
                     ppq0 = get_ppq(node0)
                     ppq_factor = info0['duration'] / ppq0 if ppq0 > 0 else 0.125
                     
                     # 1. Leading Gap (Backwards)
                     current_end = info0['start']
                     for k in range(idx0 - 1, -1, -1):
                         el = elements[k]
                         dur = get_ppq(el) * ppq_factor
                         start = current_end - dur
                         add_rest_to_map(el, start, dur, info0)
                         current_end = start

                     # 2. Internal Gaps (Interpolation)
                     for k in range(len(sync_indices) - 1):
                        i_start = sync_indices[k]
                        i_end = sync_indices[k+1]
                        
                        if i_end > i_start + 1:
                            start_node = elements[i_start]
                            end_node = elements[i_end]
                            
                            info1 = midi_map.get(get_id(start_node))
                            info2 = midi_map.get(get_id(end_node))
                            if not info1 or not info2: continue

                            t1 = info1['start'] + info1['duration']
                            t2 = info2['start']
                            total_time = max(0, t2 - t1)
                            
                            gap_elements = elements[i_start+1 : i_end]
                            total_ppq = sum(get_ppq(e) for e in gap_elements)
                            
                            if total_ppq > 0:
                                ip_factor = total_time / total_ppq
                                current_t = t1
                                for e in gap_elements:
                                    dur_sec = get_ppq(e) * ip_factor
                                    add_rest_to_map(e, current_t, dur_sec, info1)
                                    current_t += dur_sec
                     
                     # 3. Trailing Gap (Forwards)
                     idx_last = sync_indices[-1]
                     node_last = elements[idx_last]
                     info_last = midi_map.get(get_id(node_last))
                     ppq_last = get_ppq(node_last)
                     if ppq_last > 0: ppq_factor = info_last['duration'] / ppq_last
                     
                     current_start = info_last['start'] + info_last['duration']
                     for k in range(idx_last + 1, len(elements)):
                         el = elements[k]
                         dur = get_ppq(el) * ppq_factor
                         add_rest_to_map(el, current_start, dur, info_last)
                         current_start += dur
        except Exception as e: 
            print(f"MEI Timing Exception: {e}")

        # DEBUG FILE: Check extracted rests
        try:
            with open("debug_midi_map.txt", "w") as f:
                 f.write(str([(k, v['element_class']) for k, v in midi_map.items() if v.get('element_class') == 'rest']))
        except: pass

        # 5. EXTRACT DYNAMICS (Timing will be resolved spatially in Manim)
        # Parse MEI for dynamic values (p, f, etc.)
        dynam_values = {}
        try:
            for d in mei_root.findall(".//dynam"):
                did = d.get('id')
                if did:
                    # Try text content or text child
                    text = d.text
                    if not text:
                        tchild = d.find("text")
                        if tchild is not None: text = tchild.text
                    dynam_values[did] = text.strip() if text else ""
        except: pass

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
                
                dyn_val = dynam_values.get(eid, "") if cls == 'dynam' else ""
                
                midi_map[eid] = {
                    'start': 0, # Placeholder
                    'duration': 0.5,
                    'element_class': cls,
                    'part_index': p_idx,
                    'staff_n': s_n,
                    'needs_spatial_timing': True,
                    'dynamic_value': dyn_val
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
        
        # 7. EXTRACT BEAMS
        # Map Beam ID -> List of Note IDs
        beam_to_notes = {}
        try:
            for beam_el in mei_root.findall(".//beam"):
                bid = beam_el.get('id')
                # Try getting children via finding all nested notes
                child_notes = [n.get('id') for n in beam_el.findall(".//note")]
                beam_to_notes[bid] = child_notes
        except: pass

        beam_matches = re.findall(r'<g [^>]*data-id="([^"]+)" [^>]*data-class="(beam)"', self.svg_string)
        beam_count = 0
        for bid, cls in beam_matches:
            c_notes = beam_to_notes.get(bid, [])
            # Filter children present in midi_map
            valid_notes = [n for n in c_notes if n in midi_map]
            
            if valid_notes:
                # Find time span
                start_time = min(midi_map[n]['start'] for n in valid_notes)
                # End time is max of (start + duration)
                end_time = max(midi_map[n]['start'] + midi_map[n]['duration'] for n in valid_notes)
                duration = end_time - start_time
                
                # Use info from first note for part/staff
                first_info = midi_map[valid_notes[0]]
                
                midi_map[bid] = {
                    'start': start_time,
                    'duration': max(0.1, duration),
                    'element_class': 'beam',
                    'part_index': first_info.get('part_index', 0),
                    'staff_n': first_info.get('staff_n', '1')
                }
                beam_count += 1

        print(f"  - Extracted {len(all_note_ids)} notes, {slur_count} slurs, {tie_count} ties")
        print(f"  - Extracted {dyn_count} dynamic marks, {hairpin_count} hairpins")
        print(f"  - Extracted {artic_count} articulations")
        print(f"  - Extracted {beam_count} beams")
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
                    # Add start anchor (center X)
                    staff_anchors[s_n].append((mob.get_x(), midi_info['start']))
                    # Add end anchor (right X) to support durations spanning the full note
                    staff_anchors[s_n].append((mob.get_right()[0], midi_info['start'] + midi_info['duration']))
            
            for sub in mob.submobjects:
                first_pass(sub)

        first_pass(self.visual_score)
        
        # DEBUG: Check matched classes
        matched_classes = {}
        for m, rid in all_matched:
             cls = self.midi_data[rid].get('element_class', 'unknown')
             matched_classes[cls] = matched_classes.get(cls, 0) + 1
        
        try:
            with open("debug_matched_classes.txt", "w") as f:
                f.write(str(matched_classes))
        except: pass

        # Sort anchors by X
        for s in staff_anchors:
            staff_anchors[s].sort()

        # 2. PASS TWO: RESOLVE TIMING
        for mob, recovered_id in all_matched:
            midi_info = self.midi_data[recovered_id]
            e_class = midi_info.get('element_class', 'note')
            
            # Resolve spatial timing if needed (Rests from MEI Step 4.5 don't have this flag)
            if midi_info.get('needs_spatial_timing'):
                s_n = midi_info.get('staff_n', '1')
                anchors = staff_anchors.get(s_n, [])
                if not anchors: # fallback to all anchors
                    anchors = [a for s in staff_anchors.values() for a in s]
                    anchors.sort()
                
                if anchors:
                    # Find nearest LEFT anchor for start time (preserves causality)
                    # Using get_left() logic. x_target is the visual start.
                    x_target = mob.get_left()[0]
                    
                    # Filter for anchors that are to the left (or aligned) with tolerance
                    candidates = [a for a in anchors if a[0] <= x_target + 0.2]
                    
                    if candidates:
                         # Take the right-most of the candidate anchors (closest one to the left)
                        midi_info['start'] = candidates[-1][1]
                    else:
                        # Fallback: closest absolute anchor (probably the first one)
                        closest = min(anchors, key=lambda a: abs(a[0] - x_target))
                        midi_info['start'] = closest[1]
                    
                    if e_class == 'hairpin':
                        # Find nearest time for end (right side)
                        x_end = mob.get_right()[0]
                        # For end, we want the closest anchor generally, usually on the right
                        closest_end = min(anchors, key=lambda a: abs(a[0] - x_end))
                        midi_info['duration'] = max(0.1, closest_end[1] - midi_info['start'])
                    elif e_class == 'rest':
                        # Find first anchor AFTER start time to determine duration
                        try:
                            t_start = midi_info['start']
                            found_end = False
                            for a in anchors:
                                if a[1] > t_start + 0.1: # Threshold to skip jitter
                                    midi_info['duration'] = a[1] - t_start
                                    found_end = True
                                    break
                            if not found_end: midi_info['duration'] = 1.0
                        except:
                            midi_info['duration'] = 1.0
                    else:
                        midi_info['duration'] = 0.5
        
        # 3. PASS THREE: COMPUTE OPACITIES
        # Build dynamics and hairpin timelines per staff
        staff_events = {}   # staff_n -> [(time, opacity_val)]
        staff_hairpins = {} # staff_n -> [(start, end, type)]
        
        # Extended Dynamic Map
        dyn_map = {
            'pppp': 0.3, 'ppp': 0.35, 'pp': 0.4, 'p': 0.5, 'mp': 0.6,
            'mf': 0.7, 'f': 0.8, 'ff': 0.9, 'fff': 0.95, 'ffff': 1.0,
            'sf': 0.85, 'sfz': 0.85, 'rf': 0.85, 'rfz': 0.85, 
            'fp': 0.8, 'sfp': 0.8
        }
        
        # Collect events
        for mid, info in self.midi_data.items():
            s_n = info.get('staff_n', '1')
            e_class = info.get('element_class')
            
            if e_class == 'dynam' and info.get('dynamic_value'):
                if s_n not in staff_events: staff_events[s_n] = []
                
                val = info['dynamic_value']
                
                # Handle complex dynamics like fp
                if 'fp' in val:
                    # Start loud, then soft
                    op_loud = dyn_map.get('f', 0.8)
                    op_soft = dyn_map.get('p', 0.5)
                    staff_events[s_n].append((info['start'], op_loud))
                    staff_events[s_n].append((info['start'] + 0.05, op_soft))
                else:
                    op = dyn_map.get(val, 0.7)
                    staff_events[s_n].append((info['start'], op))
            
            elif e_class == 'hairpin':
                if s_n not in staff_hairpins: staff_hairpins[s_n] = []
                # info['start'] and info['duration'] are set in Pass 2
                h_type = 1 if 'cresc' in (info.get('type', '') or '') else -1 # 1 for cresc, -1 for dim? 
                # Actually need to parse type from somewhere or assume cresc if not specified? 
                # MEI usually specifies shape. Verovio class might not.
                # Assuming standard hairpin direction or checking attributes if possible.
                # For now let's infer target based on next dynamic if possible, direction matters less for interpolation "magnitude" logic 
                # unless we forcing a direction.
                # Let's assume standard closed hairpin is cresc? No, wedge type.
                # Verovio usually exports class="hairpin". We might need to check attributes for "form" or "type".
                # But let's assume valid start/end for interpolation.
                
                staff_hairpins[s_n].append((info['start'], info['start'] + info['duration']))

        # Sort timelines
        for s in staff_events: staff_events[s].sort()
        for s in staff_hairpins: staff_hairpins[s].sort()

        # Helper to get base opacity at time t
        def get_base_opacity(s_n, t):
            timeline = staff_events.get(s_n, [])
            current = 0.7 # Default
            for (dt, dop) in timeline:
                if dt <= t + 0.01:
                    current = dop
                else:
                    break
            return current

        # Assign opacity to every element
        for mid, info in self.midi_data.items():
            t = info['start']
            s_n = info.get('staff_n', '1')
            # Base level
            op = get_base_opacity(s_n, t)
            
            # Check if inside hairpin (interpolate)
            active_hairpin = None
            if s_n in staff_hairpins:
                for (h_start, h_end) in staff_hairpins[s_n]:
                    if h_start <= t <= h_end:
                        active_hairpin = (h_start, h_end)
                        break
            
            if active_hairpin:
                h_start, h_end = active_hairpin
                
                # Determine start and end opacities for the hairpin
                start_op = get_base_opacity(s_n, h_start)
                
                # Check if there is a specific dynamic target at h_end
                timeline = staff_events.get(s_n, [])
                end_op = None
                
                # Look for the FIRST event at or after h_end
                # This covers cases where the "f" is slightly after the hairpin wedge ends visually
                if timeline:
                    # Filter for events after h_end - epsilon
                    candidates = [(dt, dop) for (dt, dop) in timeline if dt >= h_end - 0.2]
                    if candidates:
                        # Take the first one found
                        cand_t, cand_op = candidates[0]
                        # Only accept if it's reasonably close (e.g. within 2 beats/seconds)
                        if cand_t - h_end < 2.0:
                            end_op = cand_op
                            
                if end_op is None:
                    # Fallback inference
                    if start_op < 0.7: end_op = min(1.0, start_op + 0.3)
                    else: end_op = max(0.3, start_op - 0.3)
                
                # Apply gradients metadata to hairpin/beam/slur/tie itself so it can slice properly
                if info.get('element_class') in ['hairpin', 'beam', 'slur', 'tie']:
                    # These elements span time, so they need start/end grad
                    info['grad_start_op'] = start_op
                    info['grad_end_op'] = end_op
                    # Base opacity is start
                    op = start_op
                else:
                    # Notes/Rests are points in time (mostly)
                    # Interpolate opacity based on note start time 't'
                    # Linear Interpolation
                    total_dur = max(0.01, h_end - h_start)
                    progress = (t - h_start) / total_dur
                    progress = max(0.0, min(1.0, progress))
                    op = start_op + (end_op - start_op) * progress
            
            info['opacity'] = op

        # 4. PASS FOUR: APPLY METADATA TO MOBJECTS
        for mob, recovered_id in all_matched:
            midi_info = self.midi_data[recovered_id]
            e_class = midi_info.get('element_class', 'note')
            
            # Apply metadata
            if e_class in ['slur', 'tie', 'hairpin', 'beam'] and not hasattr(mob, "is_slice"):
                num_slices = 100
                slices = VGroup()
                
                # Gradient values for all sliced elements
                g_start = midi_info.get('grad_start_op', midi_info.get('opacity', 0.7))
                g_end = midi_info.get('grad_end_op', g_start)
                
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
                        alpha = i / len(raw_segments)
                        s.start_time = midi_info['start'] + alpha * midi_info['duration']
                        s.part_index = midi_info.get('part_index', 0)
                        
                        # Interpolate opacity for this slice
                        s.target_opacity = g_start + (g_end - g_start) * alpha
                        slices.add(s)

                else:
                    # LOOP SLICING for Slurs/Ties/Beams (Filled Polygon slices)
                    # Slurs/Ties/Beams are usually closed paths
                    raw_polys = []
                    for i in range(num_slices):
                        try:
                            # We assume simple closed loop parameterization
                            a1 = (i / num_slices) * 0.5
                            a2 = ((i + 1) / num_slices) * 0.5
                            p1 = mob.point_from_proportion(a1)
                            p2 = mob.point_from_proportion(a2)
                            p3 = mob.point_from_proportion(1.0 - a2)
                            p4 = mob.point_from_proportion(1.0 - a1)
                            s = Polygon(p1, p2, p3, p4, stroke_width=0, fill_opacity=1.0, color=BLACK)
                            raw_polys.append(s)
                        except: pass
                    
                    raw_polys.sort(key=lambda m: m.get_center()[0])
                    for i, s in enumerate(raw_polys):
                        s.is_slice = True
                        alpha = i / len(raw_polys)
                        s.start_time = midi_info['start'] + alpha * midi_info['duration']
                        s.part_index = midi_info.get('part_index', 0)
                        # Interpolate opacity for this slice
                        s.target_opacity = g_start + (g_end - g_start) * alpha
                        slices.add(s)
                
                # CRITICAL: CLEAR PARENT GEOMETRY
                mob.points = np.zeros((0, 3))
                mob.set_fill(opacity=0)
                mob.set_stroke(opacity=0)
                
                mob.submobjects = []
                mob.add(*slices)
                mob.start_time = midi_info['start']
                mob.duration = midi_info['duration']
                mob.element_class = e_class
                mob.part_index = midi_info.get('part_index', 0)
                mob.target_opacity = midi_info.get('opacity', 0.7)
            else:
                mob.note_id = recovered_id
                mob.start_time = midi_info['start']
                mob.duration = midi_info['duration']
                mob.element_class = e_class
                mob.part_index = midi_info.get('part_index', 0)
                mob.target_opacity = midi_info.get('opacity', 0.7)
            
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
    
    def animate_playback(self, scene: Scene, colors=BLUE, color_rests=True):
        """
        Helper method to animate the score as if it's playing.
        'colors' can be a single color or a list of colors (one per instrument).
        'color_rests': if False, rests will be timed but not visually colored.
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
                # Retrieve element class
                e_cls = getattr(m, 'element_class', 'note')
                
                # Synchronization
                if t >= m.start_time:
                    # Skip coloring rests if requested
                    if e_cls == 'rest' and not color_rests:
                        # Ensure it stays black (or base color)
                        m.set_fill(BLACK, opacity=1.0)
                        m.set_stroke(BLACK, opacity=1.0)
                        return

                    # Retrieve calculated dynamic opacity
                    op = getattr(m, 'target_opacity', 0.7)
                    
                    # Use set_color for slices (Polygons/Lines) and set_fill for notes
                    if hasattr(m, "is_slice"):
                        m.set_color(col)
                        # For lines, set_stroke is key. For polygons, set_fill.
                        # Since we now use Lines for hairpins and Polygons for slurs:
                        m.set_stroke(col, opacity=op) # Affects Lines
                        m.set_fill(col, opacity=op)   # Affects Polygons
                    else:
                        m.set_fill(col, opacity=op)
                        m.set_stroke(col, opacity=op)
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
        
        if self.scrolling:
            self.clear_updaters()
    
    def animate_playback(self, scene: Scene, colors=BLUE, color_rests=True, pan_score=None):
        """
        Helper method to animate the score as if it's playing.
        'colors' can be a single color or a list of colors (one per instrument).
        'color_rests': if False, rests will be timed but not visually colored.
        'pan_score': if True, moves the score so the current note is centered. Defaults to self.scrolling.
        """
        if pan_score is None:
            pan_score = self.scrolling

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
        
        # Setup Scrolling if requested
        if pan_score:
            # Build Time -> X Map
            time_x_map = []
            for m in timed_elements:
                try:
                    # Use center x
                    time_x_map.append((m.start_time, m.get_center()[0]))
                except: pass
            
            # Sort by time
            time_x_map.sort(key=lambda x: x[0])
            
            # Extract arrays
            times = [tx[0] for tx in time_x_map]
            xs = [tx[1] for tx in time_x_map]
            
            if not times: return

            original_origin = self.get_center()
            # Capture ORIGINAL boundaries (Absolute coordinates at start)
            orig_left = self.get_left()[0]
            orig_right = self.get_right()[0]
            
            # Use Linear Regression to find the ideal constant velocity
            # Target X(t) = slope * t + intercept
            if len(times) > 1:
                slope, intercept = np.polyfit(times, xs, deg=1)
            elif len(times) == 1:
                slope, intercept = 0, xs[0]
            else:
                slope, intercept = 0, 0
            
            def scroll_updater(mob):
                t = time_tracker.get_value()
                # 1. Calculate ideal position (where the active note is)
                ideal_target_x = slope * t + intercept
                
                # 2. Define Camera Constraints
                # We want the camera to never show empty space beyond margins.
                # Screen width is approx 14.22 (config.frame_width).
                # Half width is ~7.11.
                half_width = config.frame_x_radius
                margin = 0.5 # Small buffer
                
                # The "Camera X" corresponds to resulting Center X (0) in the shifted world.
                # So if we shift by (Original - Target), the point at Target becomes Origin.
                # We want to LIMIT Target (the point that becomes Origin).
                
                # Min Target: The point that, when moved to Origin, puts Left Edge at -HalfWidth + Margin.
                # If Target moves to 0, Left Edge moves to (Left - Target).
                # We want (Left - Target) <= -HalfWidth + Margin => Target >= Left + HalfWidth - Margin.
                min_target_x = orig_left + half_width - margin
                
                # Max Target: The point that, when moved to Origin, puts Right Edge at +HalfWidth - Margin.
                # We want (Right - Target) >= HalfWidth - Margin => Target <= Right - HalfWidth + Margin.
                max_target_x = orig_right - half_width + margin
                
                # If content is smaller than screen, center it
                if max_target_x < min_target_x:
                    actual_target_x = (orig_left + orig_right) / 2
                else:
                    actual_target_x = np.clip(ideal_target_x, min_target_x, max_target_x)
                
                # 3. Move Score
                # Shift = Original_Origin - Actual_Target
                # (Because Original_Origin corresponds to the coordinate that WAS at center originally)
                # Actually, simply: We want the point `actual_target_x` to be at `original_origin[0]`.
                # Current pos of that point is (`actual_target_x` + current_shift).
                # We set new pos: `new_center = original_origin - (actual_target_x - original_origin[0_component])`?
                # No.
                # The vector `V` such that `Point + V = Origin`.
                # `V = Origin - Point`.
                # If we want `Point` (actual_target_x, 0, 0) to be at `Origin` (0,0,0) (assuming centered at start).
                # Then `shift = -actual_target_x`.
                # `mob.move_to(original_origin + shift)`.
                
                shift_x = original_origin[0] - actual_target_x
                
                current_center = mob.get_center()
                mob.move_to([shift_x, current_center[1], current_center[2]])

            self.add_updater(scroll_updater)

        # Determine highlighting color and apply updaters
        for element in timed_elements:
            # Pick color for this instrument
            p_idx = getattr(element, 'part_index', 0)
            target_color = colors[p_idx % len(colors)]
            
            def update_element(m, dt, col=target_color):
                t = time_tracker.get_value()
                # Retrieve element class
                e_cls = getattr(m, 'element_class', 'note')
                
                # Synchronization
                if t >= m.start_time:
                    # Skip coloring rests if requested
                    if e_cls == 'rest' and not color_rests:
                        # Ensure it stays black (or base color)
                        m.set_fill(BLACK, opacity=1.0)
                        m.set_stroke(BLACK, opacity=1.0)
                        return

                    # Retrieve calculated dynamic opacity
                    op = getattr(m, 'target_opacity', 0.7)
                    
                    # Use set_color for slices (Polygons/Lines) and set_fill for notes
                    if hasattr(m, "is_slice"):
                        m.set_color(col)
                        # For lines, set_stroke is key. For polygons, set_fill.
                        # Since we now use Lines for hairpins and Polygons for slurs:
                        m.set_stroke(col, opacity=op) # Affects Lines
                        m.set_fill(col, opacity=op)   # Affects Polygons
                    else:
                        m.set_fill(col, opacity=op)
                        m.set_stroke(col, opacity=op)
                else:
                    m.set_fill(BLACK, opacity=1.0)
                    m.set_stroke(BLACK, opacity=1.0)
            
            element.add_updater(update_element)
        
        # Total animation duration
        # We add the 0.5 lead-in + 0.5 buffer at the end
        max_end = max([e.start_time + getattr(e, 'duration', 0.1) for e in timed_elements])
        total_time = max_end + 1.0
        
        # Animate the time tracker (pass 'scene' to play)
        scene.play(time_tracker.animate.set_value(max_end + 0.5), run_time=total_time, rate_func=linear)
        
        # Cleanup
        for element in timed_elements:
            element.clear_updaters()
        
        if pan_score:
            self.clear_updaters()
