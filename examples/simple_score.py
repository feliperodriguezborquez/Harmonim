# examples/simple_score.py

import sys
import os

# Add the project root to the Python path to allow importing 'harmonim'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from harmonim.scene import Scene
from harmonim.notation import Note

def main():
    """
    Creates and renders a simple musical score.
    """
    # 1. Create a scene
    scene = Scene(output_filename="my_first_score")

    # 2. Add musical elements
    scene.add(Note(pitch="c'", duration=4))
    scene.add(Note(pitch="g'", duration=4))
    scene.add(Note(pitch="a'", duration=2))
    scene.add(Note(pitch="g'", duration=2))


    # 3. Render the scene
    scene.render()

if __name__ == "__main__":
    main()
