from manim import *
from harmonim.verovio_score import VerovioScore

class BeamDemo(Scene):
    def construct(self):
        # 1. Setup Score
        score = VerovioScore(
            r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\beam_test.musicxml"
        )
        score.scale(0.8)
        score.set_width(12)
        score.move_to(ORIGIN)
        
        # 2. Add to Scene
        self.add(score)
        
        # 3. Animate
        # Just play the animation
        score.animate_playback(self, colors=[TEAL, ORANGE])
        
        self.wait(5)
