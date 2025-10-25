# harmonim/renderer.py

import subprocess
import os
from typing import List
from .notation import Note

class Renderer:
    """Handles the rendering of musical elements using LilyPond."""

    def __init__(self, output_filename: str = "output"):
        """
        Initializes the Renderer.

        Args:
            output_filename: The base name for the output files (without extension).
        """
        self.output_filename = output_filename
        self.ly_filename = f"{output_filename}.ly"

    def generate_lilypond_string(self, elements: List[Note]) -> str:
        """
        Generates a complete LilyPond file string from a list of musical elements.
        """
        notes_string = " ".join([element.to_lilypond() for element in elements])
        
        # Basic LilyPond structure
        return f'''
\\version "2.24.4"
\\header {{
  tagline = ""  % Removes the LilyPond tagline
}}
\\score {{
  {{
    {notes_string}
  }}
  \\layout {{ }}
  \\midi {{ }}
}}
'''

    def render(self, elements: List[Note]):
        """
        Renders the musical elements into an image.

        1. Generates the LilyPond string.
        2. Writes it to a .ly file.
        3. Calls LilyPond to compile the .ly file into a PNG image.
        """
        ly_string = self.generate_lilypond_string(elements)

        with open(self.ly_filename, "w") as f:
            f.write(ly_string)

        print(f"Generated LilyPond file: {self.ly_filename}")

        # Run LilyPond command
        command = [
            "lilypond",
            "-dbackend=cairo",
            "--png",
            "-o",
            self.output_filename,
            self.ly_filename,
        ]
        
        print(f"Running command: {' '.join(command)}")

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print("LilyPond output:\n", result.stdout)
            if result.stderr:
                print("LilyPond errors:\n", result.stderr)
            
            # os.remove(self.ly_filename)
            
            print(f"Successfully generated score image: {self.output_filename}.png")

        except FileNotFoundError:
            print("Error: 'lilypond' command not found.")
            print("Please ensure LilyPond is installed and in your system's PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing LilyPond:")
            print(f"Command: {' '.join(e.cmd)}")
            print(f"Return code: {e.returncode}")
            print(f"Output:\n{e.stdout}")
            print(f"Errors:\n{e.stderr}")
