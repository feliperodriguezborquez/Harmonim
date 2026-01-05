import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from manim import *
from harmonim.io.musicxml import MusicXMLParser
from harmonim.renderers.manim_renderer import ManimRenderer
from harmonim.renderers.lilypond_renderer import LilyPondRenderer
from harmonim.renderers.verovio_renderer import VerovioRenderer
from harmonim.core.animator import MusicXMLAnimator

class MusicXMLScene(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        # Get input file from environment variable or default
        xml_path = os.environ.get("HARMONIM_INPUT", "test_score.musicxml")
        
        if not os.path.exists(xml_path):
            print(f"Error: File {xml_path} not found.")
            return

        # 0. Pre-process to ensure IDs
        from harmonim.utils.xml_utils import ensure_unique_ids
        processed_xml_path = ensure_unique_ids(xml_path)
        print(f"Processed XML saved to: {processed_xml_path}")

        # 1. Parse
        parser = MusicXMLParser()
        staff_group = parser.parse(processed_xml_path)
        
        # 2. Render
        # Try to use VerovioRenderer, fallback to LilyPond, then Manim
        try:
            renderer = VerovioRenderer()
            score_mobject = renderer.render_score(processed_xml_path)
            print("Using VerovioRenderer")
        except Exception as e:
            print(f"Verovio rendering failed: {e}. Falling back to LilyPondRenderer.")
            try:
                renderer = LilyPondRenderer()
                score_mobject = renderer.render(staff_group)
                print("Using LilyPondRenderer")
            except Exception as e:
                print(f"LilyPond rendering failed: {e}. Falling back to ManimRenderer.")
                renderer = ManimRenderer()
                score_mobject = renderer.render(staff_group)
            
        score_mobject.move_to(ORIGIN)
        
        # Scale down if it's too big, or up if it's small?
        # User wants zoom.
        # Let's scale to fit width - 4 (more margin = smaller?) No, width - 1 is max width.
        # If we want zoom, we want the score to be larger relative to screen.
        # But if it's too wide, it goes off screen.
        # Maybe scale to fit height?
        # Or just scale up a bit if it fits?
        # Let's try scaling to width - 2.
        if score_mobject.width > config.frame_width - 2:
            score_mobject.scale_to_fit_width(config.frame_width - 2)
        else:
            # If it's small, scale it up to fill some width
            score_mobject.scale_to_fit_width(config.frame_width - 2)
            
        self.add(score_mobject)
        
        # 3. Animate
        animator = MusicXMLAnimator(staff_group, renderer)
        animation = animator.create_animation(color=RED)
        
        self.play(animation)
        self.wait(1)
