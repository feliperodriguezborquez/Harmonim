"""
VerovioScore - A VGroup that intelligently maps MIDI data to Manim mobjects.

This class solves the ID mapping problem by:
1. Rendering SVG with Verovio
2. Extracting timing/MIDI data from Verovio
3. Loading the SVG in Manim
4. Linking mobjects to their MIDI data via spatial/index matching
5. Attaching metadata as mobject attributes
"""
from manim import *
import verovio
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np


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
        
        # 4. Parse XML structure to know note positions/order
        self.note_info = self._parse_note_structure()
        
        print(f"Found {len(self.note_info)} notes in score")
        print(f"MIDI data for {len(self.midi_data)} elements")
        
        # 5. Load visual in Manim
        temp_path = Path("output") / "temp_verovio_score.svg"
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(self.svg_string)
        
        self.visual_score = SVGMobject(str(temp_path))
        
        # 6. THE MAGIC LINKING
        self._attach_metadata_to_mobjects()
        
        # 7. Add to this VGroup
        self.add(self.visual_score)
        
        # 8. Apply default styling
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
    
    def _parse_note_structure(self) -> Dict:
        """
        Parse SVG XML to find notes and global content bounds.
        """
        root = ET.fromstring(self.svg_string)
        notes = {}
        
        # Track global bounds of ALL elements to align with Manim
        self.svg_content_min_x = float('inf')
        self.svg_content_max_x = float('-inf')
        self.svg_content_min_y = float('inf')
        self.svg_content_max_y = float('-inf')
        
        def update_bounds(x, y):
            self.svg_content_min_x = min(self.svg_content_min_x, x)
            self.svg_content_max_x = max(self.svg_content_max_x, x)
            self.svg_content_min_y = min(self.svg_content_min_y, y)
            self.svg_content_max_y = max(self.svg_content_max_y, y)

        def find_elements(element, current_x=0, current_y=0):
            # Check for x/y attributes
            e_x = float(element.get('x', 0))
            e_y = float(element.get('y', 0))
            
            # Check for transform="translate(x, y)"
            transform = element.get('transform', '')
            if 'translate' in transform:
                try:
                    # Simple parsing: translate(x, y) or translate(x)
                    # Remove 'translate(' and ')'
                    t_str = transform[transform.find('translate(')+10 : transform.find(')')]
                    parts = t_str.replace(',', ' ').split()
                    if len(parts) >= 1:
                        e_x += float(parts[0])
                    if len(parts) >= 2:
                        e_y += float(parts[1])
                except:
                    pass
            
            # Update current cumulative position
            abs_x = current_x + e_x
            abs_y = current_y + e_y
            
            # Update bounds if this element has position
            if e_x or e_y:
                update_bounds(abs_x, abs_y)
            
            # Check for notes
            data_class = element.get('class', '') 
            elem_id = element.get('data-id') or element.get('id')
            
            if elem_id and 'note' in data_class:
                # Found a note group. Find its center.
                # CRITICAL: Only use elements within <g class="notehead"> to avoid
                # including accidentals, stems, etc. in the centroid calculation
                center_x = 0
                center_y = 0
                count = 0
                
                # Helper to find notehead elements only
                def find_notehead_elements(node, cx, cy, inside_notehead=False):
                    nonlocal center_x, center_y, count
                    
                    # Check if this is a notehead group
                    node_class = node.get('class', '')
                    is_notehead_group = 'notehead' in node_class
                    
                    # Update flag: we're inside a notehead group
                    if is_notehead_group:
                        inside_notehead = True
                    
                    # Local transform
                    lx = float(node.get('x', 0))
                    ly = float(node.get('y', 0))
                    tf = node.get('transform', '')
                    if 'translate' in tf:
                        try:
                            t_str = tf[tf.find('translate(')+10 : tf.find(')')]
                            parts = t_str.replace(',', ' ').split()
                            if len(parts) >= 1: lx += float(parts[0])
                            if len(parts) >= 2: ly += float(parts[1])
                        except: pass
                    
                    acx = cx + lx
                    acy = cy + ly
                    
                    # Only count <use> elements that are inside a notehead group
                    # This excludes accidentals, stems, flags, etc.
                    if inside_notehead and node.tag.endswith('use'):
                        center_x += acx
                        center_y += acy
                        count += 1
                        update_bounds(acx, acy)
                    
                    # Recurse to children
                    for child in node:
                        find_notehead_elements(child, acx, acy, inside_notehead)
                
                find_notehead_elements(element, abs_x, abs_y)
                
                if count > 0:
                    center_x /= count
                    center_y /= count
                    notes[elem_id] = {'x': center_x, 'y': center_y}
            
            # Recurse
            for child in element:
                find_elements(child, abs_x, abs_y)
        
        find_elements(root)
        return notes

    def _attach_metadata_to_mobjects(self):
        """
        Attach MIDI metadata to Manim mobjects using INCREMENTAL MATCHING.
        
        Strategy:
        1. Sort notes by (Y position, start time, X position) for logical ordering
        2. For each note, find closest available mobject
        3. Assign metadata and REMOVE from candidate pool
        4. Continue with remaining mobjects
        
        This eliminates ambiguities by ensuring each mobject is matched only once.
        """
        # 1. Get all leaf mobjects from Manim
        available_mobjects = []
        def flatten(mob):
            if isinstance(mob, VMobject) and len(mob.submobjects) == 0:
                available_mobjects.append(mob)
            for sub in mob.submobjects:
                flatten(sub)
        flatten(self.visual_score)
        
        if not available_mobjects: 
            print("No mobjects found!")
            return

        # 2. Manim Global Bounds
        manim_xs = [m.get_center()[0] for m in available_mobjects]
        manim_ys = [m.get_center()[1] for m in available_mobjects]
        m_min_x, m_max_x = min(manim_xs), max(manim_xs)
        m_min_y, m_max_y = min(manim_ys), max(manim_ys)
        m_width = m_max_x - m_min_x
        m_height = m_max_y - m_min_y
        
        # 3. SVG Global Bounds (calculated in parsing)
        s_min_x, s_max_x = self.svg_content_min_x, self.svg_content_max_x
        s_min_y, s_max_y = self.svg_content_min_y, self.svg_content_max_y
        s_width = s_max_x - s_min_x
        s_height = s_max_y - s_min_y
        
        print(f"Manim Bounds: X[{m_min_x:.2f}, {m_max_x:.2f}] Y[{m_min_y:.2f}, {m_max_y:.2f}]")
        print(f"SVG Bounds:   X[{s_min_x:.2f}, {s_max_x:.2f}] Y[{s_min_y:.2f}, {s_max_y:.2f}]")
        print(f"Total mobjects: {len(available_mobjects)}")
        print(f"Total notes with MIDI: {len([n for n in self.note_info.keys() if n in self.midi_data])}")
        
        # 4. Prepare notes with normalized coordinates and MIDI data
        notes_to_match = []
        for note_id, coords in self.note_info.items():
            if note_id not in self.midi_data: 
                continue
            
            midi_info = self.midi_data[note_id]
            
            # Normalize SVG coords to Manim space
            norm_x = (coords['x'] - s_min_x) / s_width if s_width > 0 else 0.5
            norm_y = (coords['y'] - s_min_y) / s_height if s_height > 0 else 0.5
            
            target_x = m_min_x + (norm_x * m_width)
            target_y = m_max_y - (norm_y * m_height)
            
            notes_to_match.append({
                'note_id': note_id,
                'midi': midi_info,
                'svg_coords': coords,
                'target_point': np.array([target_x, target_y, 0]),
                'svg_y': coords['y'],  # For sorting by staff
                'start_time': midi_info['start'],
            })
        
        # 5. INCREMENTAL MATCHING: Sort notes by (Y position, time, X position)
        # This processes notes in logical reading order: top staff first, left to right, chronologically
        notes_to_match.sort(key=lambda n: (n['svg_y'], n['start_time'], n['svg_coords']['x']))
        
        print(f"Matching {len(notes_to_match)} notes incrementally...")
        
        matched = 0
        failed_matches = []
        
        for i, note_data in enumerate(notes_to_match):
            if not available_mobjects:
                print(f"Warning: Ran out of mobjects! {len(notes_to_match) - matched} notes unmatched.")
                break
            
            # Find closest mobject among AVAILABLE candidates
            best_dist = float('inf')
            best_mob = None
            best_idx = -1
            
            for idx, mob in enumerate(available_mobjects):
                dist = np.linalg.norm(mob.get_center() - note_data['target_point'])
                if dist < best_dist:
                    best_dist = dist
                    best_mob = mob
                    best_idx = idx
            
            # Assign metadata to best match
            if best_mob:
                best_mob.note_id = note_data['note_id']
                best_mob.start_time = note_data['midi']['start']
                best_mob.duration = note_data['midi']['duration']
                best_mob.pitch = note_data['midi']['pitch']
                
                # DEBUG: Show match info
                if i < 5 or i >= len(notes_to_match) - 5:  # First/last 5
                    print(f"  Note {i+1}/{len(notes_to_match)}: {note_data['note_id']} -> matched (dist={best_dist:.3f})")
                
                # REMOVE from available pool
                available_mobjects.pop(best_idx)
                matched += 1
            else:
                failed_matches.append(note_data)
                print(f"  Note {i+1}/{len(notes_to_match)}: {note_data['note_id']} -> FAILED to match!")
        
        print(f"Successfully matched {matched}/{len(notes_to_match)} notes")
        print(f"Remaining unassigned mobjects: {len(available_mobjects)}")
        
        if failed_matches:
            print(f"\n!!! {len(failed_matches)} NOTES FAILED TO MATCH:")
            for note_data in failed_matches:
                print(f"  - {note_data['note_id']}: pitch={note_data['midi']['pitch']}, start={note_data['midi']['start']:.2f}s")
    
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
    
    def animate_playback(self, scene: Scene, color=BLUE):
        """
        Helper method to animate the score as if it's playing.
        
        Usage in Scene:
            score = VerovioScore("song.musicxml")
            scene.add(score)
            score.animate_playback(scene)
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
