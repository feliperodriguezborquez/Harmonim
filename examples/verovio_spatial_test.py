from manim import *
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from harmonim.verovio_score import VerovioScore

class VerovioSpatialTest(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        # Path to MusicXML (using the one from previous demos)
        xml_path = os.path.join(os.path.dirname(__file__), "comprehensive_score.musicxml")
        
        if not os.path.exists(xml_path):
            # Fallback if file doesn't exist, create a simple one or error
            print(f"Error: {xml_path} not found.")
            return

        # Create the score
        score = VerovioScore(xml_path)
        score.scale(1.5)
        score.move_to(ORIGIN)
        
        self.add(score)
        
        # Debug Visualization
        # We will iterate through the mapped notes and draw a dot where Manim thinks they are
        # vs where Verovio says they are (if we can extract that).
        
        # For now, just animate to see if any mapping happened (likely 0 with current code)
        score.animate_playback(self, color=RED)
        
        self.wait(1)
