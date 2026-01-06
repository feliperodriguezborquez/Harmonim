from manim import *
from harmonim.verovio_score import VerovioScore

class ComplexOrchestralAnimation(Scene):
    def construct(self):
        # Set background to white for a professional look
        self.camera.background_color = WHITE
        
        # Load the complex score
        xml_path = r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\examples\orchestral_test.musicxml"
        score = VerovioScore(xml_path)
        
        # Scale to fit frame width nicely
        score.width = config.frame_width - 2
        if score.height > config.frame_height - 2:
            score.height = config.frame_height - 2
        
        self.add(score)
        
        # Define 4 distinct colors for the 4 instruments
        orchestra_colors = [
            BLUE_D,    # Flute
            RED_D,     # Violin
            GREEN_D,   # Cello
            PURPLE_D   # Piano (both staves will be Purple)
        ]
        
        # Start playback animation
        score.animate_playback(self, colors=orchestra_colors)
        
        self.wait(2)

if __name__ == "__main__":
    # Command to run: manim -ql test_complex_orchestra.py ComplexOrchestralAnimation
    pass
