
import verovio
import xml.etree.ElementTree as ET

tk = verovio.toolkit()
tk.loadFile(r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\demo.musicxml")
mei = tk.getMEI()

# Parse MEI
root = ET.fromstring(mei)
# Strip namespaces
for elem in root.iter():
    elem.tag = elem.tag.split('}')[-1]

print("MEI Structure:")
parts = []
# In MEI, parts are staffGrp
for staff_grp in root.findall(".//staffGrp"):
    # If it has staffDef children, it's a part (or a group of staves)
    # A single instrument part usually is a staffGrp with one or more staffDef
    labels = staff_grp.get('label')
    staves = [s.get('n') for s in staff_grp.findall("staffDef")]
    if staves:
        parts.append({"label": labels, "staves": staves})

print(parts)
