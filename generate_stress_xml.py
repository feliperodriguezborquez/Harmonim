import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_note(step, octave, duration_type, duration_val, voice=1, beam=None, slur=None, dynam=None):
    note = ET.Element('note')
    
    pitch = ET.SubElement(note, 'pitch')
    ET.SubElement(pitch, 'step').text = step
    ET.SubElement(pitch, 'octave').text = str(octave)
    
    ET.SubElement(note, 'duration').text = str(duration_val)
    ET.SubElement(note, 'voice').text = str(voice)
    ET.SubElement(note, 'type').text = duration_type
    
    if beam:
        ET.SubElement(note, 'beam', number="1").text = beam
        
    notations = None
    if slur:
        notations = ET.SubElement(note, 'notations') if notations is None else notations
        ET.SubElement(notations, 'slur', type=slur, number="1")
    
    if dynam:
        # MusicXML usually puts dynamics in <direction>, not <note>, but let's stick to notes mainly
        # For this generator, we'll keep it simple: notes only.
        pass

    return note

def create_stress_test():
    score = ET.Element('score-partwise', version="3.1")
    pl = ET.SubElement(score, 'part-list')
    
    # Part 1: Violin
    sp1 = ET.SubElement(pl, 'score-part', id="P1")
    ET.SubElement(sp1, 'part-name').text = "Violin"
    
    # Part 2: Cello
    sp2 = ET.SubElement(pl, 'score-part', id="P2")
    ET.SubElement(sp2, 'part-name').text = "Cello"
    
    # -- BUILD PART 1 (Violin) --
    p1 = ET.SubElement(score, 'part', id="P1")
    
    measures = 30
    
    # Pattern: 
    # 1-10: Fast semiquaver runs (Beams)
    # 11-20: Long notes with Slurs
    # 21-30: Mixed articulation (Staccato)
    
    steps = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    
    for m in range(1, measures + 1):
        measure = ET.SubElement(p1, 'measure', number=str(m))
        
        # Attributes for first measure
        if m == 1:
            attrs = ET.SubElement(measure, 'attributes')
            divs = ET.SubElement(attrs, 'divisions')
            divs.text = "4" # 16th note = 1
            key = ET.SubElement(attrs, 'key')
            ET.SubElement(key, 'fifths').text = "0"
            time = ET.SubElement(attrs, 'time')
            ET.SubElement(time, 'beats').text = "4"
            ET.SubElement(time, 'beat-type').text = "4"
            clef = ET.SubElement(attrs, 'clef')
            ET.SubElement(clef, 'sign').text = "G"
            ET.SubElement(clef, 'line').text = "2"
            
        # GENERATE CONTENT
        if m <= 10: 
            # 16th note runs (16 notes per measure)
            # 4 beams of 4 notes
            for b in range(4):
                for i in range(4):
                    step_idx = (m + b*4 + i) % 7
                    octave = 5 + ((m + b) // 7) % 2
                    
                    bm_type = "begin" if i==0 else ("end" if i==3 else "continue")
                    n = create_note(steps[step_idx], octave, "16th", 1, beam=bm_type)
                    measure.append(n)
        elif m <= 20:
            # Whole notes with slurs
            n = create_note(steps[m % 7], 5, "whole", 16)
            
            # Add slur start/stop every 2 measures
            notations = ET.SubElement(n, 'notations')
            if m % 2 != 0:
                ET.SubElement(notations, 'slur', type="start", number="1")
                # Add simple dynamic direction
                direction = ET.SubElement(measure, 'direction', placement="below")
                dt = ET.SubElement(direction, 'direction-type')
                if (m-10) % 4 == 1:
                     ET.SubElement(dt, 'wedge', type="crescendo", number="1")
                elif (m-10) % 4 == 3:
                     ET.SubElement(dt, 'wedge', type="diminuendo", number="1")
            else:
                ET.SubElement(notations, 'slur', type="stop", number="1")
                # Stop wedge
                direction = ET.SubElement(measure, 'direction', placement="below")
                dt = ET.SubElement(direction, 'direction-type')
                ET.SubElement(dt, 'wedge', type="stop", number="1")
                
            measure.append(n)
        else:
            # Quarter notes with articulations
            for i in range(4):
                step_idx = (m*i) % 7
                n = create_note(steps[step_idx], 4, "quarter", 4)
                notations = ET.SubElement(n, 'notations')
                art = ET.SubElement(notations, 'articulations')
                if i % 2 == 0:
                    ET.SubElement(art, 'staccato')
                else:
                    ET.SubElement(art, 'accent')
                measure.append(n)

    # -- BUILD PART 2 (Cello) --
    p2 = ET.SubElement(score, 'part', id="P2")
    for m in range(1, measures + 1):
        measure = ET.SubElement(p2, 'measure', number=str(m))
        if m == 1:
            attrs = ET.SubElement(measure, 'attributes')
            divs = ET.SubElement(attrs, 'divisions')
            divs.text = "4"
            clef = ET.SubElement(attrs, 'clef')
            ET.SubElement(clef, 'sign').text = "F"
            ET.SubElement(clef, 'line').text = "4"
        
        # Simple accompaniment: Whole notes or Half notes
        if m <= 10:
            # Two half notes
            n1 = create_note('C', 3, "half", 8)
            n2 = create_note('G', 3, "half", 8)
            measure.extend([n1, n2])
        elif m <= 20:
             # Whole notes to support violin slurs
             n = create_note('C', 2, "whole", 16)
             measure.append(n)
        else:
            # Walking bass quarters
            steps_c = ['C', 'E', 'G', 'B']
            for i in range(4):
                n = create_note(steps_c[i], 3, "quarter", 4)
                measure.append(n)

    # Write to file
    xmlstr = minidom.parseString(ET.tostring(score)).toprettyxml(indent="   ")
    with open("examples/stress_test.musicxml", "w", encoding="utf-8") as f:
        f.write(xmlstr)

if __name__ == "__main__":
    create_stress_test()
