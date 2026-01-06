
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
    if eid and eid.startswith('P') and len(eid) < 8:
        if elem.tag == 'staffDef':
            s_n = elem.get('n')
            if s_n: parts_found[eid] = [s_n]
        elif elem.tag == 'staffGrp':
            staves = [sd.get('n') for sd in elem.findall(".//staffDef")]
            if staves: parts_found[eid] = staves

print("--- MEI ANALYSIS ---")
print(f"Parts found: {parts_found}")

sorted_part_ids = sorted(parts_found.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
staff_to_part_idx = {}
for p_idx, p_id in enumerate(sorted_part_ids):
    for s_n in parts_found[p_id]:
        staff_to_part_idx[s_n] = p_idx
print(f"Staff to Part Index: {staff_to_part_idx}")

svg = tk.renderToSVG(1)
svg_clean = re.sub(' xmlns="[^"]+"', '', svg, count=1)
svg_root = ET.fromstring(svg_clean)

id_to_staff_n = {}
print("\n--- SVG ANALYSIS ---")
for staff in svg_root.findall(".//g[@data-class='staff']"):
    s_id = staff.get('data-id')
    s_attrs = tk.getElementAttr(s_id)
    if isinstance(s_attrs, str): s_attrs = json.loads(s_attrs)
    s_n = s_attrs.get('n')
    print(f"Staff data-id='{s_id}' n='{s_n}'")
    # Take first note child as sample
    note = staff.find(".//g[@data-class='note']")
    if note is not None:
        n_id = note.get('data-id')
        print(f"  Sample Note ID: {n_id}")
        # Does our logic find progress?
        for elem in staff.iter():
            e_id = elem.get('data-id')
            if e_id: id_to_staff_n[e_id] = s_n

# Sample check
some_note_id = list(id_to_staff_n.keys())[0] if id_to_staff_n else None
if some_note_id:
    sn = id_to_staff_n.get(some_note_id)
    pi = staff_to_part_idx.get(sn)
    print(f"\nFinal Check: Note {some_note_id} -> Staff {sn} -> Part Index {pi}")
else:
    print("\nFAILED: No notes found in SVG staff groups")
