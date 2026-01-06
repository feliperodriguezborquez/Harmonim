from manim import *
from harmonim.verovio_score import VerovioScore
import os

class StressTestDemo(Scene):
    def construct(self):
        # 1. Setup Score
        score = VerovioScore(
            r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\stress_test.musicxml",
            scrolling=True
        )
        
        # Scale for visibility - height constraint is key for infinite scroll
        # 6 is good for 2 staves.
        score.visual_score.scale_to_fit_height(6)
        
        score.move_to(ORIGIN)
        
        # 2. Add to Scene
        self.camera.background_color = WHITE
        self.add(score)
        
        # 3. Animate
        palette = [TEAL, MAROON] # Violin (Teal), Cello (Maroon)
        
        # Since this is a stress test, we let it play all the way
        score.animate_playback(self, colors=palette)
        
        self.wait(2)
