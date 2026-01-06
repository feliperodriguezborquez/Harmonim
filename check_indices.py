
from harmonim.verovio_score import VerovioScore
from manim import *

# Fake scene for testing
class Test(Scene):
    def construct(self):
        xml_path = r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\orchestral_test.musicxml"
        score = VerovioScore(xml_path)
        
        print("\n--- MIDI DATA PART INDICES ---")
        for eid, info in score.midi_data.items():
            print(f"ID: {eid}, Class: {info.get('element_class')}, Part Index: {info.get('part_index')}")

Test().render()
