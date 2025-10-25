# harmonim/scene.py

from .notation import Note
from .renderer import Renderer
from typing import List

class Scene:
    """
    A scene that contains musical elements and can be rendered.
    """
    def __init__(self, output_filename: str = "score"):
        """
        Initializes the Scene.

        Args:
            output_filename: The base name for the output files.
        """
        self.elements: List[Note] = []
        self.renderer = Renderer(output_filename)

    def add(self, element: Note):
        """
        Adds a musical element to the scene.
        """
        # For now, we only accept Note objects. This can be expanded later.
        if isinstance(element, Note):
            self.elements.append(element)
        else:
            print(f"Warning: Element of type {type(element)} is not currently supported.")

    def render(self):
        """
        Renders the scene to an image.
        """
        print("--- Starting Harmonim Render ---")
        if not self.elements:
            print("Scene is empty. Nothing to render.")
            return
            
        self.renderer.render(self.elements)
        print("--- Harmonim Render Finished ---")
