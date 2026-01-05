"""
Debug script to inspect note detection and matching
"""
import verovio
import os
import xml.etree.ElementTree as ET

# Load the score
xml_path = os.path.join(os.path.dirname(__file__), "comprehensive_score.musicxml")

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

if not tk.loadFile(xml_path):
    print(f"Error loading {xml_path}")
    exit(1)

# Get SVG
svg_string = tk.renderToSVG(1)

# Extract MIDI data
print("\n=== MIDI DATA ===")
timemap = tk.renderToTimemap()

all_note_ids = set()
for event in timemap:
    all_note_ids.update(event.get('on', []))

print(f"Total note IDs from timemap: {len(all_note_ids)}")

midi_data = {}
for note_id in all_note_ids:
    try:
        info = tk.getMIDIValuesForElement(note_id)
        if info:
            midi_data[note_id] = {
                'start': info.get('time', 0) / 1000.0,
                'duration': info.get('duration', 0) / 1000.0,
                'pitch': info.get('pitch', 60)
            }
            print(f"{note_id}: start={midi_data[note_id]['start']:.2f}s, pitch={midi_data[note_id]['pitch']}, duration={midi_data[note_id]['duration']:.2f}s")
    except:
        pass

# Parse SVG structure
print("\n=== SVG STRUCTURE ===")
root = ET.fromstring(svg_string)

notes_in_svg = {}

def find_notes(element, depth=0):
    data_class = element.get('class', '')
    elem_id = element.get('data-id') or element.get('id')
    
    if elem_id and 'note' in data_class:
        # Check if it has a notehead
        has_notehead = False
        for child in element.iter():
            child_class = child.get('class', '')
            if 'notehead' in child_class:
                has_notehead = True
                break
        
        notes_in_svg[elem_id] = {
            'has_notehead': has_notehead,
            'has_midi': elem_id in midi_data,
            'class': data_class
        }
        
        status = "[OK]" if (has_notehead and elem_id in midi_data) else "[MISS]"
        print(f"{status} {elem_id}: notehead={has_notehead}, midi={elem_id in midi_data}, class={data_class}")
    
    for child in element:
        find_notes(child, depth + 1)

find_notes(root)

print(f"\nTotal notes in SVG: {len(notes_in_svg)}")
print(f"Notes with MIDI: {len(midi_data)}")
print(f"Notes with notehead: {sum(1 for n in notes_in_svg.values() if n['has_notehead'])}")
print(f"Notes with both: {sum(1 for id, n in notes_in_svg.items() if n['has_notehead'] and id in midi_data)}")

# Identify missing notes
print("\n=== MISSING FROM MATCHING ===")
for note_id, props in notes_in_svg.items():
    if props['has_notehead'] and not props['has_midi']:
        print(f"Note {note_id} has notehead but NO MIDI data")
    elif not props['has_notehead'] and props['has_midi']:
        print(f"Note {note_id} has MIDI but NO notehead")
