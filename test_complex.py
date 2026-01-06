from manim import *
from harmonim.verovio_score import VerovioScore

class ComplexDemo(Scene):
    def construct(self):
        # 1. Setup Score
        score = VerovioScore(
            r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\complex_test.musicxml"
        )
        score.scale(0.6)
        score.set_width(12)
        score.move_to(ORIGIN)
        
        # 2. Add to Scene
        self.camera.background_color = WHITE
        self.add(score)
        
        # 3. Animate
        # Play using distinct colors for Piano (Teal) and Violin (Maroon)
        score.animate_playback(self, colors=[TEAL, MAROON])
        
        self.wait(2)
