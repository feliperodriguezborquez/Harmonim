# harmonim/notation.py

class Note:
    """Represents a single musical note."""
    def __init__(self, pitch: str, duration: int):
        """
        Initializes a Note.

        Args:
            pitch: The pitch of the note in LilyPond format (e.g., "c'", "a,").
            duration: The duration of the note (e.g., 4 for a quarter note, 8 for an eighth).
        """
        if not isinstance(pitch, str) or not pitch:
            raise ValueError("Pitch must be a non-empty string.")
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError("Duration must be a positive integer.")
            
        self.pitch = pitch
        self.duration = duration

    def to_lilypond(self) -> str:
        """Converts the note to its LilyPond string representation."""
        return f"{self.pitch}{self.duration}"
