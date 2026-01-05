"""
Verovio Color Mapper - Uses unique colors as ID carriers.

This module implements the "color hack" for robust ID mapping:
1. Generate SVG from Verovio
2. Inject unique colors for each note (encode ID in RGB)
3. Load in Manim (colors are preserved)
4. Read mobject colors to recover IDs
5. Restore original colors
"""
import xml.etree.ElementTree as ET
from typing import Dict, Tuple


class ColorIDMapper:
    """Maps IDs to unique colors and vice versa."""
    
    def __init__(self):
        self.id_to_color: Dict[str, str] = {}
        self.color_to_id: Dict[str, str] = {}
        self._color_counter = 1
    
    def get_unique_color(self, element_id: str) -> str:
        """Generate a unique color for an ID."""
        if element_id in self.id_to_color:
            return self.id_to_color[element_id]
        
        # Encode counter as RGB
        # Use slight variations to make them imperceptibly different
        # Start from (0,0,1) to avoid pure black
        r = (self._color_counter >> 16) & 0xFF
        g = (self._color_counter >> 8) & 0xFF
        b = self._color_counter & 0xFF
        
        # Ensure it's not pure black (which might be default)
        if r == 0 and g == 0 and b == 0:
            b = 1
        
        color_hex = f"#{r:02x}{g:02x}{b:02x}"
        
        self.id_to_color[element_id] = color_hex
        self.color_to_id[color_hex] = element_id
        
        self._color_counter += 1
        
        return color_hex
    
    def get_id_from_rgb(self, r: float, g: float, b: float) -> str:
        """Recover ID from RGB values (0-1 range)."""
        # Convert from 0-1 to 0-255
        r_int = int(round(r * 255))
        g_int = int(round(g * 255))
        b_int = int(round(b * 255))
        
        color_hex = f"#{r_int:02x}{g_int:02x}{b_int:02x}"
        
        return self.color_to_id.get(color_hex, None)


def inject_colors_to_svg(svg_string: str, element_ids: list, color_mapper: ColorIDMapper) -> str:
    """
    Inject unique colors into SVG for specified element IDs.
    
    Args:
        svg_string: Original SVG from Verovio
        element_ids: List of IDs to colorize (typically note IDs)
        color_mapper: ColorIDMapper instance
        
    Returns:
        Modified SVG string with unique colors
    """
    root = ET.fromstring(svg_string)
    
    # Register namespace to preserve it
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    
    # Find and color each element
    _inject_colors_recursive(root, element_ids, color_mapper)
    
    # Convert back to string
    return ET.tostring(root, encoding='unicode')


def _inject_colors_recursive(element: ET.Element, target_ids: list, color_mapper: ColorIDMapper):
    """Recursively inject colors."""
    element_id = element.get('id')
    
    if element_id in target_ids:
        # Get unique color for this ID
        unique_color = color_mapper.get_unique_color(element_id)
        
        # Inject color as fill AND stroke
        # We need to ensure Manim picks it up
        element.set('fill', unique_color)
        element.set('stroke', unique_color)
        
        # Also add to style if exists
        style = element.get('style', '')
        # Remove existing fill/stroke from style
        style_parts = [p.strip() for p in style.split(';') if p.strip()]
        style_parts = [p for p in style_parts if not p.startswith('fill') and not p.startswith('stroke')]
        style_parts.append(f'fill:{unique_color}')
        style_parts.append(f'stroke:{unique_color}')
        element.set('style', ';'.join(style_parts))
    
    # Recurse
    for child in element:
        _inject_colors_recursive(child, target_ids, color_mapper)


def extract_note_ids_from_svg(svg_string: str) -> list:
    """Extract all note element IDs from SVG."""
    root = ET.fromstring(svg_string)
    note_ids = []
    
    def find_notes(elem):
        data_class = elem.get('data-class', '')
        elem_id = elem.get('id')
        
        if 'note' in data_class and elem_id:
            note_ids.append(elem_id)
        
        for child in elem:
            find_notes(child)
    
    find_notes(root)
    return note_ids
