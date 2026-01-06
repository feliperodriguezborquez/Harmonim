# Harmonim

Harmonim is a powerful Python library for automating high-quality musical score animations using [Manim](https://www.manim.community/) and [Verovio](https://www.verovio.org/).

It takes **MusicXML** files as input and renders them as precise, aesthetically pleasing animations where notes, dynamics, and articulations light up in synchronization with the music.

## Features

*   **MusicXML Import**: Simply provide a `.musicxml` file, and Harmonim handles the rendering.
*   **Intelligent Synchronization**:
    *   **Notes & Chords**: Colored precisely when played.
    *   **Rests**: Respects musical timing of silence (optionally visible or invisible).
    *   **Beams**: Progressive animation mirroring the duration of the beamed group.
    *   **Slurs & Ties**: Smoothly animated over their full duration.
    *   **Hairpins (Crescendo/Diminuendo)**: Dynamic opacity changes (fade in/out) synchronized with the score.
    *   **Dynamics & Articulations**: Visual emphasis for *p*, *f*, accents, staccatos, etc.
*   **Multi-Instrument Support**: Automatically handles multiple staves/parts with independent coloring.
*   **Professional Engraving**: Leveraging Verovio and the SMuFL-compliant Bravura font for publication-quality sheet music.
*   **Manim Integration**: Returns a standard Manim `VGroup` that can be manipulated (moved, scaled, faded) like any other object.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/feliperodriguezborquez/Harmonim.git
    cd Harmonim
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Requirements: `manim`, `verovio`, `numpy`.*

## Quick Start

Harmonim revolves around the `VerovioScore` class.

### 1. Create a MusicXML File
Export your score from Musescore, Finale, or Dorico as `.musicxml`.

### 2. Create a Manim Script (`demo.py`)

```python
from manim import *
from harmonim.verovio_score import VerovioScore

class MyScoreAnimation(Scene):
    def construct(self):
        # 1. Initialize the Score
        score = VerovioScore("path/to/my_score.musicxml")
        
        # 2. Position it
        score.scale(0.8)
        score.move_to(ORIGIN)
        
        # 3. Add to Scene
        self.camera.background_color = WHITE
        self.add(score)
        
        # 4. Animate Playback
        # 'colors' list maps to instruments (P1, P2...)
        # 'color_rests' determines if rests should be lit up (default: True)
        score.animate_playback(self, colors=[TEAL, MAROON], color_rests=False)
        
        self.wait(2)
```

### 3. Render
```bash
manim -ql demo.py MyScoreAnimation
```

## Examples

Check the `examples/` and test scripts for more advanced use cases:

*   **`test_complex.py`**: A full demonstration featuring piano and violin, chords, dynamics, and articulations.
*   **`test_rests.py`**: demonstrates precise handling of rests and syncopation.
*   **`test_beams.py`**: Shows beam animation.

## Architecture

Harmonim uses a novel "Color Injection" technique to bridge Verovio and Manim:
1.  **Render**: Verovio renders the MusicXML to SVG.
2.  **Map**: Harmonim extracts MIDI timing and attributes from Verovio's MEI structure.
3.  **Trace**: It injects unique color IDs into the SVG elements to track them.
4.  **Reconstruct**: The SVG is loaded into Manim, and the IDs are used to bind the Manim vectors back to their musical meaning (start time, duration, part).
5.  **Animate**: Custom Updaters control opacity and color based on the animation clock.

## License

[MIT License](LICENSE)