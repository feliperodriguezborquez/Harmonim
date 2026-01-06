from manim import *
from harmonim.verovio_score import VerovioScore

class DynamicsDemo(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        xml_path = r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\dynamics_test.musicxml"
        score = VerovioScore(xml_path)
        score.width = config.frame_width - 2
        
        self.add(score)
        
        # Animate with a nice Gold color
        score.animate_playback(self, colors=GOLD_E)
        
        self.wait(2)

if __name__ == "__main__":
    # manim -ql test_dynamics.py DynamicsDemo
    pass
