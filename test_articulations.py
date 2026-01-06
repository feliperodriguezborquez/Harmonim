from manim import *
from harmonim.verovio_score import VerovioScore

class ArticulationsDemo(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        xml_path = r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\articulations_test.musicxml"
        score = VerovioScore(xml_path)
        score.width = config.frame_width - 2
        
        self.add(score)
        
        # Animate
        score.animate_playback(self, colors=[GOLD, RED])
        self.wait(1)
