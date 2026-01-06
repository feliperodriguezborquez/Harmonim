
import verovio
import re

tk = verovio.toolkit()
tk.setOptions({"svgHtml5": True})
tk.loadFile(r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\dynamics_test.musicxml")
svg = tk.renderToSVG(1)

matches = re.findall(r'<g [^>]*data-id="([^"]+)" [^>]*data-class="(hairpin|dynam)"', svg)
for eid, cls in matches:
    attrs = tk.getElementAttr(eid)
    print(f"ID: {eid} {cls} -> {attrs}")
