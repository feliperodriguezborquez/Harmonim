from manim import *
from harmonim.verovio_score import VerovioScore

class RestDemo(Scene):
    def construct(self):
        # 1. Setup Score
        score = VerovioScore(
            r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\rests_test.musicxml"
        )
        score.scale(0.8)
        score.set_width(12)
        score.move_to(ORIGIN)
        
        # 2. Add to Scene
        self.camera.background_color = WHITE
        self.add(score)
        
        # 3. Animate
        # Use simple color, but disable rest coloring
        score.animate_playback(self, colors=[TEAL], color_rests=False)
        
        self.wait(2)
