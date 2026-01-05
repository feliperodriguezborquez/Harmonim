"""
LilyPond renderer for Harmonim.
"""
import os
import subprocess
import tempfile
import uuid
from typing import Any, Dict, Optional, List, Union
from manim import SVGMobject, VMobject, VGroup, WHITE, BLACK, ORIGIN
from ..elements.staff import Staff, StaffGroup
from ..elements.note import Note, Rest
from ..elements.base import MusicElement
from .base import Renderer, RenderOptions

class LilyPondRenderer(Renderer):
    """Renderer that uses LilyPond to generate SVGs."""
    
    def __init__(self, options: Optional[RenderOptions] = None):
        super().__init__(options)
        self.rendered_elements_map = {}
        
    def render(self, element: Union[Staff, StaffGroup], **kwargs) -> SVGMobject:
        """Render a Staff or StaffGroup to a Manim SVGMobject."""
        
        # 1. Generate IDs for all elements we want to track
        id_mapping = {}
        elements_to_track = []
        
        if isinstance(element, StaffGroup):
            for staff in element.staves:
                elements_to_track.extend(staff.elements)
        elif isinstance(element, Staff):
            elements_to_track.extend(element.elements)
            
        for el in elements_to_track:
            # Generate a unique ID safe for LilyPond/SVG
            # LilyPond strings should be simple.
            unique_id = f"harmonim_{uuid.uuid4().hex}"
            id_mapping[el] = unique_id
            
        # 2. Generate LilyPond code
        lilypond_code = self._generate_lilypond_file(element, id_mapping)
        
        # 3. Compile to SVG
        svg_file = self._compile_lilypond(lilypond_code)
        
        if not svg_file:
            raise RuntimeError("Failed to compile LilyPond code.")
            
        # 4. Load SVG into Manim
        # Manim's SVGMobject loads the SVG.
        # We need to find the sub-mobjects that correspond to our IDs.
        # Unfortunately, standard SVGMobject doesn't easily expose ID mapping.
        # But we can try to parse the SVG file ourselves to find which paths have which IDs,
        # or we can use a custom SVGMobject that preserves IDs.
        
        # Let's try to use a standard SVGMobject and then traverse it?
        # No, the structure is flattened or grouped by hierarchy, not by ID.
        # However, if we use `SVGMobject(..., unpack_groups=False)`, maybe?
        
        # Actually, Manim's SVGMobject logic is complex.
        # A better approach might be to use `manim.mobject.svg.svg_mobject.SVGMobject` 
        # and inspect `submobjects`.
        
        # Let's try a hack: 
        # We can parse the SVG file to find the order of paths and their IDs.
        # Manim loads paths in order.
        # If we know the ID of the Nth path, we can map it.
        
        svg_obj = SVGMobject(svg_file)
        
        # Map IDs to Manim objects
        # We need to parse the SVG XML to find IDs.
        import xml.etree.ElementTree as ET
        tree = ET.parse(svg_file)
        root = tree.getroot()
        
        # Namespace map
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        
        # Find all elements with 'id' attribute, in document order
        # Note: Manim might skip some elements (defs, invisible, etc.)
        # This is risky.
        
        # Alternative:
        # We can't easily map back without a robust SVG parser that matches Manim's logic.
        # BUT, we can try to assign the ID to the mobject if we patch Manim or use a custom class.
        
        # For now, let's assume we can't easily get the ID back from Manim's SVGMobject directly.
        # Wait! If we use `SVGMobject`, it has a `submobjects` list.
        # If we can correlate the XML nodes to the submobjects...
        
        # Let's try a different approach for the mapping.
        # If we can't map perfectly, we can't animate specific notes.
        # But we MUST animate specific notes.
        
        # Let's use a custom SVGMobject that stores IDs.
        # Or, we can use `xml.etree` to find the IDs and their bounding boxes? No.
        
        # Let's try to use `BeautifulSoup` or `xml` to extract IDs and their order.
        # Manim processes `<path>`, `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<polyline>`, `<polygon>`.
        # It ignores `<g>` for creating mobjects (it groups them).
        
        # If we flatten the SVG XML to a list of renderable elements, we might match them to `svg_obj.submobjects`.
        # This is the standard way to do it in Manim when IDs are needed.
        
        # Let's implement a helper to extract IDs in order.
        ids_in_order = self._extract_ids_from_svg(svg_file)
        
        # Now we have a list of IDs.
        # svg_obj might be a VGroup of VGroups. We need to flatten it to match the XML elements?
        # SVGMobject usually creates a hierarchy matching the groups.
        # If we flatten both, we might match.
        
        flat_mobjects = self._flatten_mobjects(svg_obj)
        
        # Filter ids_in_order to only include those that Manim likely rendered
        # (e.g. paths, not groups).
        # This is still tricky.
        
        # Let's try to match by count.
        if len(flat_mobjects) != len(ids_in_order):
            print(f"Warning: Mismatch in SVG parsing. Manim found {len(flat_mobjects)} objects, XML found {len(ids_in_order)} elements.")
            # Fallback or partial match?
        
        # Map IDs to objects
        self.id_to_mobject = {}
        for i, mobj in enumerate(flat_mobjects):
            if i < len(ids_in_order):
                svg_id = ids_in_order[i]
                if svg_id:
                    self.id_to_mobject[svg_id] = mobj
        
        # Now map back to Harmonim elements
        for element, unique_id in id_mapping.items():
            if unique_id in self.id_to_mobject:
                self.rendered_elements_map[element] = self.id_to_mobject[unique_id]
        
        # Center and set color
        svg_obj.move_to(ORIGIN)
        svg_obj.set_color(BLACK) # Set to black for white background
        
        print(f"Extracted {len(ids_in_order)} IDs from SVG.")
        print(f"Mapped {len(self.rendered_elements_map)} elements out of {len(id_mapping)} tracked elements.")
        
        return svg_obj

    def _generate_lilypond_file(self, element: Union[Staff, StaffGroup], id_mapping: Dict[MusicElement, str]) -> str:
        """Generate the full LilyPond source code."""
        content = element.to_lilypond(id_mapping=id_mapping)
        
        header = r"""
\version "2.24.0"
#(set-global-staff-size 20)

\paper {
  indent = 0\mm
  ragged-right = ##f
  line-width = 150\mm
  oddHeaderMarkup = ##f
  evenHeaderMarkup = ##f
  oddFooterMarkup = ##f
  evenFooterMarkup = ##f
  top-margin = 10\mm
  bottom-margin = 10\mm
  left-margin = 10\mm
  right-margin = 10\mm
  print-page-number = ##f
}

\header {
  tagline = ##f
}
"""
        return f"{header}\n{content}"

    def _compile_lilypond(self, code: str) -> Optional[str]:
        """Compile LilyPond code to SVG and return the file path."""
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.ly', mode='w', delete=False) as f:
            f.write(code)
            ly_path = f.name
            
        # Output prefix
        base_name = os.path.splitext(ly_path)[0]
        
        # Run LilyPond
        # -dbackend=svg
        cmd = ["lilypond", "-dbackend=svg", "-dno-point-and-click", f"--output={base_name}", ly_path]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"LilyPond compilation failed: {e.stderr.decode()}")
            return None
        finally:
            # Cleanup .ly file
            try:
                os.remove(ly_path)
            except:
                pass
                
        # LilyPond adds .svg extension
        svg_path = f"{base_name}.svg"
        if os.path.exists(svg_path):
            return svg_path
        return None

    def _extract_ids_from_svg(self, svg_path: str) -> List[Optional[str]]:
        """Extract IDs from SVG elements in document order, propagating group IDs."""
        import xml.etree.ElementTree as ET
        
        ids = []
        
        # Recursive function to traverse XML
        def traverse(node, current_id=None):
            # Check for ID on this node
            node_id = node.get('id')
            if node_id:
                current_id = node_id
            
            tag = node.tag.split('}')[-1] # Remove namespace
            
            # If it's a renderable element, record the ID (current or inherited)
            if tag in ['path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon']:
                ids.append(current_id)
            
            for child in node:
                traverse(child, current_id)
                
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
            traverse(root)
        except Exception as e:
            print(f"Error parsing SVG: {e}")
            
        return ids

    def _flatten_mobjects(self, mobject: VMobject) -> List[VMobject]:
        """Flatten a hierarchy of mobjects into a list of renderable mobjects."""
        flat = []
        if mobject.submobjects:
            for sub in mobject.submobjects:
                flat.extend(self._flatten_mobjects(sub))
        else:
            flat.append(mobject)
        return flat
