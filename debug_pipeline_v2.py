
import verovio
import xml.etree.ElementTree as ET
import re
import json

tk = verovio.toolkit()
tk.setOptions({"svgHtml5": True})
tk.loadFile(r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\orchestral_test.musicxml")

mei = tk.getMEI()
mei_clean = re.sub(r' xmlns(:[a-z]+)?="[^"]+"', '', mei)
mei_clean = re.sub(r'([a-z]+):id=', r'id=', mei_clean)
mei_root = ET.fromstring(mei_clean)

parts_found = {} # {part_id: [staff_n]}
for elem in mei_root.iter():
    eid = elem.get('id')
    if eid and eid.startswith('P'):
        tag = elem.tag
        if tag == 'staffDef':
            s_n = elem.get('n')
            if s_n: parts_found[eid] = [s_n]
        elif tag == 'staffGrp':
            staves = [sd.get('n') for sd in elem.findall(".//staffDef")]
            if staves: parts_found[eid] = staves

print(f"Parts found: {parts_found}")

svg = tk.renderToSVG(1)
svg_clean = re.sub(' xmlns="[^"]+"', '', svg, count=1)
svg_root = ET.fromstring(svg_clean)

id_to_staff_n = {}
for staff in svg_root.findall(".//g[@class='staff']"):
    s_id = staff.get('data-id')
    s_attrs = tk.getElementAttr(s_id)
    if isinstance(s_attrs, str): s_attrs = json.loads(s_attrs)
    s_n = s_attrs.get('n')
    for elem in staff.iter():
        e_id = elem.get('data-id')
        if e_id: id_to_staff_n[e_id] = s_n

# Check some note IDs
notes = re.findall(r'data-id="([^"]+)" [^>]*data-class="note"', svg)
print(f"Total notes in SVG: {len(notes)}")
if notes:
    for n in notes[:5]:
        sn = id_to_staff_n.get(n)
        print(f"Note {n} -> Staff {sn}")
