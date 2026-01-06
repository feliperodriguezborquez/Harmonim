
import verovio
import re

tk = verovio.toolkit()
tk.loadData(open(r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\articulations_test.musicxml", "r").read())
tk.setOptions({
    "font": "Bravura",
    "svgViewBox": True,
    "svgHtml5": True,
    "header": "none",
    "footer": "none"
})
svg = tk.renderToSVG(1)

# Find all 'g' elements with classes that might be articulations

matches = re.findall(r'<g [^>]*data-id="([^"]+)" [^>]*data-class="(artic)"', svg)
print(f"Found {len(matches)} articulations")

for eid, cls in matches:
    attrs = tk.getElementAttr(eid)
    print(f"ID: {eid}, Class: {cls}, Attrs: {attrs}")
