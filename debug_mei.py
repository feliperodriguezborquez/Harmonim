
import verovio
import re
import xml.etree.ElementTree as ET

tk = verovio.toolkit()
tk.loadFile(r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\articulations_test.musicxml")
mei = tk.getMEI()

mei_clean = re.sub(r' xmlns(:[a-z]+)?="[^"]+"', '', mei)
mei_clean = re.sub(r'([a-z]+):id=', r'id=', mei_clean)

print(f"MEI length: {len(mei_clean)}")
print(f"First 500 chars: {mei_clean[:500]}")


root = ET.fromstring(mei_clean)

# Valid IDs from previous step: n50f4b4

# Iterate through all notes and print children
for note in root.findall(".//note"):
    print(f"Note ID: {note.get('id')}")
    for child in note:
        print(f"  Child: {child.tag}, ID: {child.get('id')}, Attrs: {child.attrib}")
