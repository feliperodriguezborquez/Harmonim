
from manim import *
from harmonim.verovio_score import VerovioScore
import os

class TestSlurTieAnimation(Scene):
    def construct(self):
        # Set white background for "professional" look
        self.camera.background_color = WHITE
        
        musicxml_path = r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\demo.musicxml"
        
        if not os.path.exists(musicxml_path):
            self.add(Text(f"File not found: {musicxml_path}", color=RED))
            return
            
        score = VerovioScore(musicxml_path)
        score.set_color(BLACK)
        
        # Scale score to fit WIDTH instead of height, with some padding
        # This prevents the "too much zoom" look for short scores
        score.width = config.frame_width - 2
        
        # If the score is still too tall, cap the height
        if score.height > config.frame_height - 1:
            score.height = config.frame_height - 1
            
        self.add(score)
        
        # Animate with different colors per instrument
        # Piano (P1) will be RED, Flute (P2) will be GOLD
        score.animate_playback(self, colors=[RED, GOLD])
        self.wait(2)

if __name__ == "__main__":
    # To run: manim -p -ql test_slurs.py TestSlurTieAnimation
    pass
