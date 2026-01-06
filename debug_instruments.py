
import verovio
import json
import re

tk = verovio.toolkit()
tk.setOptions({
    "scale": 50,
    "adjustPageHeight": True,
    "font": "Bravura",
    "svgViewBox": True,
    "svgHtml5": True,
    "header": "none",
    "footer": "none"
})

musicxml_path = r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\demo.musicxml"
tk.loadFile(musicxml_path)
svg = tk.renderToSVG(1)

# Find some note IDs
note_ids = re.findall(r'data-id="([^"]+)" data-class="note"', svg)

for eid in note_ids[:5]:
    attrs = tk.getElementAttr(eid)
    print(f"Note {eid}: {attrs}")
    
    # Let's see if we can get the staff
    # Verovio SVG hierarchy: part -> measure -> staff -> layer -> note
    # We can use regex to find the parent staff ID
    staff_match = re.search(r'<g [^>]*data-id="([^"]+)" [^>]*data-class="staff">.*?data-id="' + eid + '"', svg, re.DOTALL)
    if staff_match:
        staff_id = staff_match.group(1)
        staff_attrs = tk.getElementAttr(staff_id)
        print(f"  Parent Staff {staff_id}: {staff_attrs}")
