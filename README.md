# Harmonim

Harmonim is a Python library for programmatically generating and animating musical scores, built on top of [Manim](https://www.manim.community/). It allows you to create high-quality, professional-looking musical animations using code.

## Features

*   **Programmatic Score Generation**: Define notes, rests, clefs, key signatures, and time signatures using Python objects.
*   **Manim Integration**: Seamlessly render musical elements as Manim `Mobject`s for easy animation.
*   **SMuFL Support**: Uses the [Bravura](https://github.com/steinbergmedia/bravura) font (SMuFL compliant) for professional music engraving aesthetics.
*   **Complex Scores**: Supports grand staves, multiple voices, and automatic layout adjustments.
*   **Customizable**: Control colors, spacing, and styling to fit your visual needs.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/feliperodriguezborquez/Harmonim.git
    cd Harmonim
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You must have [Manim](https://docs.manim.community/en/stable/installation.html) installed on your system (including FFmpeg and LaTeX).*

3.  **Font Setup:**
    Harmonim uses the Bravura font. Ensure `harmonim/assets/fonts/Bravura.otf` is present. The library attempts to register it automatically.

## Usage

### Basic Example

Create a simple animation of a single note:

```bash
manim -pql examples/animation_example.py SimpleNoteAnimation
```

### Rendering a Complex Score

To render a full grand staff with key signatures, time signatures, and notes:

```bash
manim -pqh tests/test_complex_score.py ComplexScore
```

*   `-p`: Preview the video after rendering.
*   `-qh`: Render in High Quality (1080p60). Use `-ql` for low quality during development.

### Code Example

```python
from harmonim.elements import Note, Rest, Staff, StaffGroup, Clef, KeySignature, TimeSignature
from harmonim.renderers.manim_renderer import ManimRenderer

# Define a Staff
staff = Staff(clef=Clef('treble'))
staff.add_element(TimeSignature('4/4'))
staff.add_element(Note('C', 4, 1.0)) # Middle C, Quarter note
staff.add_element(Note('E', 4, 1.0))
staff.add_element(Note('G', 4, 1.0))
staff.add_element(Rest(1.0))

# Render with Manim
# (Inside a Manim Scene)
renderer = ManimRenderer()
staff_mobject = renderer.render(staff)
self.add(staff_mobject)
```

## Project Structure

*   `harmonim/`: Core library package.
    *   `elements/`: Musical element definitions (Note, Staff, Clef, etc.).
    *   `renderers/`: Rendering logic (currently Manim).
    *   `core/`: Configuration and SMuFL mappings.
    *   `assets/`: Fonts and other static assets.
*   `examples/`: Example scripts.
*   `tests/`: Unit and visual tests.

## License

[MIT License](LICENSE)