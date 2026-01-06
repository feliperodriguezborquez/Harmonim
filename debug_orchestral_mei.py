
import verovio
import xml.etree.ElementTree as ET

tk = verovio.toolkit()
tk.loadFile(r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\orchestral_test.musicxml")
mei = tk.getMEI()

root = ET.fromstring(mei)
# Namespaces
ns = {'mei': 'http://www.music-encoding.org/ns/mei', 'xml': 'http://www.w3.org/XML/1998/namespace'}

staff_to_part = {}
all_staff_defs = root.findall(".//mei:staffDef", ns)

for sd in all_staff_defs:
    s_n = sd.get('n')
    s_id = sd.get('{http://www.w3.org/XML/1998/namespace}id')
    
    # Check if ID is a part ID (usually starts with P)
    if s_id and s_id.startswith('P') and len(s_id) < 5:
        staff_to_part[s_n] = s_id
    else:
        # Check parents
        # This is harder with ET. Let's use a mapping approach.
        pass

# Better approach: find all elements with an ID starting with P
parts_map = {} # {part_id: [staff_n]}
for elem in root.iter():
    eid = elem.get('{http://www.w3.org/XML/1998/namespace}id')
    if eid and eid.startswith('P') and len(eid) < 5:
        # If it's a staffDef, it's a single staff part
        if elem.tag.endswith('staffDef'):
            parts_map[eid] = [elem.get('n')]
        # If it's a staffGrp, it's a multi-staff part
        elif elem.tag.endswith('staffGrp'):
            staves = [sd.get('n') for sd in elem.findall(".//mei:staffDef", ns)]
            parts_map[eid] = staves

print("Discovered Parts Mapping:")
print(parts_map)
