
import verovio
import re

tk = verovio.toolkit()
tk.setOptions({
    "scale": 50, 
    "adjustPageHeight": True,
    "svgHtml5": True
})
tk.loadFile(r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\orchestral_test.musicxml")
svg = tk.renderToSVG(1)

# Look for 'part' in the SVG
part_matches = re.findall(r'<g [^>]*class="[^"]*part[^"]*"[^>]*>', svg)
print(f"Part matches found: {len(part_matches)}")
for m in part_matches[:5]:
    print(f"  {m}")

# Look for 'staff' in the SVG
staff_matches = re.findall(r'<g [^>]*class="[^"]*staff[^"]*"[^>]*>', svg)
print(f"Staff matches found: {len(staff_matches)}")
for m in staff_matches[:5]:
    print(f"  {m}")
