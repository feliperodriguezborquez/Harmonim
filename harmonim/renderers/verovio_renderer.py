"""
Verovio renderer for Harmonim.
"""
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional, Union, List
from pathlib import Path

import verovio
from manim import SVGMobject, VMobject, VGroup, Mobject, BLACK

from .base import Renderer, RenderOptions
from ..core.config import config
from .verovio_color_mapper import ColorIDMapper, inject_colors_to_svg, extract_note_ids_from_svg

class VerovioRenderer(Renderer):
    """Renderer that uses Verovio to generate SVGs and maps them to Manim objects."""
    
    def __init__(self, options: Optional[RenderOptions] = None):
        """Initialize the Verovio renderer."""
        super().__init__(options)
        self.tk = verovio.toolkit()
        # Set default options for Verovio
        self.tk.setOptions({
            "scale": 50,
            "adjustPageHeight": True,
            "font": "Bravura",
            "svgViewBox": True,
            "svgHtml5": True, # Adds data-id and data-class
            "header": "none",
            "footer": "none"
        })
        
        self.id_to_mobject: Dict[str, Mobject] = {}
        self.rendered_elements_map: Dict[Any, Mobject] = {} # For compatibility
        self.svg_mobject: Optional[SVGMobject] = None
        self.color_mapper: Optional[ColorIDMapper] = None  # For color-based mapping

    def render(self, element: Any, **kwargs) -> Any:
        """
        Verovio renders the whole score at once, not individual elements.
        Use render_score() instead.
        """
        raise NotImplementedError("VerovioRenderer renders the entire score. Use render_score().")

    def render_score(self, musicxml_path: Union[str, Path]) -> SVGMobject:
        """
        Render a MusicXML file to a Manim SVGMobject with ID mapping.
        
        Args:
            musicxml_path: Path to the MusicXML file.
            
        Returns:
            A Manim SVGMobject representing the score.
        """
        musicxml_path = str(musicxml_path)
        
        # 1. Load into Verovio
        if not self.tk.loadFile(musicxml_path):
            raise RuntimeError(f"Could not load MusicXML file: {musicxml_path}")
            
        # 2. Render to SVG string
        svg_string_original = self.tk.renderToSVG(1)
        
        # 3. Convert data-id to id attributes
        svg_string_with_ids = self._convert_data_ids_to_ids(svg_string_original)
        
        # 4. COLOR INJECTION - The key to robust ID mapping!
        # Extract note IDs from SVG
        note_ids = extract_note_ids_from_svg(svg_string_with_ids)
        print(f"DEBUG: Found {len(note_ids)} notes to colorize")
        
        # Create color mapper
        self.color_mapper = ColorIDMapper()
        
        # Inject unique colors for each note
        svg_string_colored = inject_colors_to_svg(svg_string_with_ids, note_ids, self.color_mapper)
        
        # 5. Save and load in Manim
        temp_svg_path = Path(self.options.output_dir) / "temp_verovio_render.svg"
        temp_svg_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_svg_path, "w", encoding="utf-8") as f:
            f.write(svg_string_colored)
            
        self.svg_mobject = SVGMobject(str(temp_svg_path))
        
        # 6. Map IDs by reading colors from mobjects!
        self.map_ids_by_color(self.svg_mobject)
        
        # 7. Restore original colors (black)
        self._fix_styles(self.svg_mobject)
        
        # Cleanup temp file
        if not self.options.debug:
            try:
                os.remove(temp_svg_path)
            except OSError:
                pass
                
        return self.svg_mobject
    
    def _convert_data_ids_to_ids(self, svg_string: str) -> str:
        """
        Convert data-id attributes to id attributes in SVG.
        
        Verovio generates notes with data-id="..." but Manim only preserves standard id="..." attributes.
        This function converts data-id to id so we can map notes correctly.
        
        Strategy:
        1. Parse the SVG XML
        2. For each element with data-id, also set it as id (if id doesn't exist)
        3. Return modified SVG string
        """
        root = ET.fromstring(svg_string)
        self._add_ids_recursive(root)
        
        # Convert back to string
        result = ET.tostring(root, encoding='unicode')
        return result
    
    def _add_ids_recursive(self, element: ET.Element):
        """Recursively add id attributes from data-id."""
        # Check if element has data-id
        data_id = element.get('data-id')
        existing_id = element.get('id')
        
        if data_id and not existing_id:
            # Set the id attribute to match data-id
            element.set('id', data_id)
        
        # Recurse to children
        for child in element:
            self._add_ids_recursive(child)


    def _fix_styles(self, mobject: Mobject):
        """
        Fixes visibility issues with imported SVGs.
        """
        if isinstance(mobject, VMobject):
            # Force BLACK color for everything
            mobject.set_color(BLACK)
            
            try:
                current_sw = mobject.get_stroke_width()
            except TypeError:
                current_sw = 0
            
            # If it has no fill, it MUST have a stroke
            if mobject.get_fill_opacity() == 0:
                if current_sw < 1.5:
                    mobject.set_stroke(width=1.5)
            
            # If it has a stroke, ensure it's thick enough
            if current_sw > 0 and current_sw < 1.5:
                mobject.set_stroke(width=1.5)

        for sub in mobject.submobjects:
            self._fix_styles(sub)

    def map_ids_by_color(self, svg_mobject: SVGMobject):
        """
        Map IDs by reading colors from mobjects (color hack).
        
        This is the "decode" step:
        1. Flatten all mobjects
        2. Read their fill/stroke colors
        3. Use color_mapper to recover the ID
        4. Build id_to_mobject mapping
        """
        if not self.color_mapper:
            print("WARNING: No color mapper available, cannot map IDs")
            return
        
        self.id_to_mobject = {}
        
        # Flatten all mobjects
        all_mobjects = []
        self._flatten_all(svg_mobject, all_mobjects)
        
        print(f"DEBUG: Scanning {len(all_mobjects)} mobjects for unique colors")
        
        mapped_count = 0
        
        for mob in all_mobjects:
            if not isinstance(mob, VMobject):
                continue
            
            # Try to read color from fill
            try:
                fill_rgb = mob.get_fill_color()
                if fill_rgb is not None and hasattr(fill_rgb, '__iter__'):
                    if len(fill_rgb) >= 3:
                        r, g, b = fill_rgb[0], fill_rgb[1], fill_rgb[2]
                        
                        # Try to recover ID
                        note_id = self.color_mapper.get_id_from_rgb(r, g, b)
                        
                        if note_id:
                            self.id_to_mobject[note_id] = mob
                            mapped_count += 1
                            continue
            except:
                pass
            
            # Try stroke color as fallback
            try:
                stroke_rgb = mob.get_stroke_color()
                if stroke_rgb is not None and hasattr(stroke_rgb, '__iter__'):
                    if len(stroke_rgb) >= 3:
                        r, g, b = stroke_rgb[0], stroke_rgb[1], stroke_rgb[2]
                        
                        note_id = self.color_mapper.get_id_from_rgb(r, g, b)
                        
                        if note_id and note_id not in self.id_to_mobject:
                            self.id_to_mobject[note_id] = mob
                            mapped_count += 1
            except:
                pass
        
        print(f"DEBUG: Successfully mapped {mapped_count} notes via color decoding")
    
    def _flatten_all(self, mobject: Mobject, result: list):
        """Recursively flatten all mobjects."""
        result.append(mobject)
        for sub in mobject.submobjects:
            self._flatten_all(sub, result)


