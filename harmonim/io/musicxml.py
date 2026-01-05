import music21
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from ..elements.staff import Staff, StaffGroup
from ..elements.note import Note, Rest
from ..elements.clef import Clef, TrebleClef, BassClef, AltoClef, TenorClef
from ..elements.key_signature import KeySignature
from ..elements.time_signature import TimeSignature
from ..elements.barline import Barline, BarlineType
from ..elements.tie import Tie

class MusicXMLParser:
    """Parses MusicXML files into Harmonim internal structures."""

    def parse(self, file_path: str) -> StaffGroup:
        """Parses a MusicXML file."""
        score = music21.converter.parse(file_path)
        
        # Sync IDs from XML to Music21 objects
        self._sync_ids(score, file_path)
        
        return self._convert_score(score)

    def _sync_ids(self, score: music21.stream.Score, file_path: str):
        """
        Manually syncs IDs from the XML file to the music21 objects.
        Music21 often ignores XML IDs, so we map them by order.
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract XML notes (flattened)
            xml_notes = []
            # We need to traverse measures to match music21's flattened order
            # Music21 flattens by part -> measure -> voice -> note
            # XML structure is Part -> Measure -> Note
            # This simple traversal should match music21's default flattening for simple scores.
            for part in root.findall("part"):
                for measure in part.findall("measure"):
                    for note in measure.findall("note"):
                        # Skip grace notes if music21 skips them? 
                        # Music21 includes grace notes.
                        # We should include everything.
                        xml_notes.append(note)
            
            # Extract Music21 notes
            m21_notes = list(score.recurse().notesAndRests)
            
            if len(xml_notes) == len(m21_notes):
                for m21_note, xml_note in zip(m21_notes, xml_notes):
                    xml_id = xml_note.get('id')
                    if xml_id:
                        m21_note.id = xml_id
            else:
                print(f"Warning: Note count mismatch (XML: {len(xml_notes)}, M21: {len(m21_notes)}). ID sync skipped.")
                
        except Exception as e:
            print(f"Warning: Failed to sync IDs: {e}")

    def _convert_score(self, score: music21.stream.Score) -> StaffGroup:
        staff_group = StaffGroup()
        
        # Iterate through parts (staves)
        for part in score.parts:
            staff = Staff()
            
            # Let's iterate through measures
            measures = part.getElementsByClass('Measure')
            
            for measure in measures:
                # Check for Clef change
                if measure.clef:
                    pass
                
                # Iterate through elements in the measure
                for element in measure:
                    if isinstance(element, music21.clef.Clef):
                        staff.clef = self._convert_clef(element)
                        
                    elif isinstance(element, music21.key.KeySignature):
                        staff.key_signature = self._convert_key_signature(element)
                        
                    elif isinstance(element, music21.meter.TimeSignature):
                        staff.time_signature = self._convert_time_signature(element)
                        
                    elif isinstance(element, music21.note.Note):
                        # Calculate absolute offset
                        abs_offset = measure.offset + element.offset
                        staff.add_element(self._convert_note(element, abs_offset))
                        
                    elif isinstance(element, music21.chord.Chord):
                        abs_offset = measure.offset + element.offset
                        staff.add_element(self._convert_chord(element, abs_offset))
                        
                    elif isinstance(element, music21.note.Rest):
                        abs_offset = measure.offset + element.offset
                        staff.add_element(self._convert_rest(element, abs_offset))
                        
                    elif isinstance(element, music21.bar.Barline):
                        pass
                
                # Add barline at end of measure
                barline_type = BarlineType.SINGLE
                if measure.rightBarline:
                    if measure.rightBarline.type == 'final':
                        barline_type = BarlineType.FINAL
                    elif measure.rightBarline.type == 'double':
                        barline_type = BarlineType.DOUBLE
                
                # Barline offset is end of measure
                barline_offset = measure.offset + measure.duration.quarterLength
                staff.add_barline(Barline(barline_type, offset=barline_offset))
            
            staff_group.add_staff(staff)
            
        return staff_group

    def _convert_clef(self, m21_clef: music21.clef.Clef) -> Clef:
        if isinstance(m21_clef, music21.clef.TrebleClef):
            return TrebleClef()
        elif isinstance(m21_clef, music21.clef.BassClef):
            return BassClef()
        elif isinstance(m21_clef, music21.clef.AltoClef):
            return AltoClef()
        elif isinstance(m21_clef, music21.clef.TenorClef):
            return TenorClef()
        return TrebleClef() # Default

    def _convert_key_signature(self, m21_key: music21.key.KeySignature) -> KeySignature:
        # Harmonim KeySignature takes a root name (e.g. 'C', 'F#')
        # music21 key has .sharps (int) or .tonic (Pitch)
        if m21_key.sharps == 0:
            return KeySignature('C')
        
        if hasattr(m21_key, 'tonic') and m21_key.tonic:
            return KeySignature(m21_key.tonic.name.replace('-', 'b'))
        
        try:
            k = m21_key.asKey()
            if k.tonic:
                return KeySignature(k.tonic.name.replace('-', 'b'))
        except:
            pass
            
        sharps = m21_key.sharps
        if sharps == 0:
            return KeySignature('C')
        
        circle_sharps = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#']
        circle_flats = ['C', 'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb']
        
        if sharps > 0 and sharps < len(circle_sharps):
            return KeySignature(circle_sharps[sharps])
        elif sharps < 0 and abs(sharps) < len(circle_flats):
            return KeySignature(circle_flats[abs(sharps)])
            
        return KeySignature('C')

    def _convert_time_signature(self, m21_time: music21.meter.TimeSignature) -> TimeSignature:
        return TimeSignature(m21_time.numerator, m21_time.denominator)

    def _convert_note(self, m21_note: music21.note.Note, offset: float = 0.0) -> Note:
        # Pitch
        pitch_name = m21_note.pitch.nameWithOctave.replace('-', 'b')
        
        # Duration
        duration = m21_note.quarterLength
        
        # Accidental
        accidental = None
        if m21_note.pitch.accidental:
            accidental = m21_note.pitch.accidental.name
            if accidental == 'natural':
                accidental = 'natural' # Explicit natural
            
        # Dot
        dot = m21_note.duration.dots > 0
        
        # Ties
        tie_start = False
        tie_stop = False
        tie_id = None
        tie_duration = 0.0
        
        if m21_note.tie:
            if m21_note.tie.type == 'start':
                tie_start = True
                import uuid
                tie_id = f"tie_{uuid.uuid4().hex}"
                tie_duration = m21_note.quarterLength
            elif m21_note.tie.type == 'stop':
                tie_stop = True
                
        # Slurs
        slur_start = False
        slur_stop = False
        slur_id = None
        slur_duration = 0.0
        
        spanners = m21_note.getSpannerSites()
        for spanner in spanners:
            if isinstance(spanner, music21.spanner.Slur):
                if spanner.isFirst(m21_note):
                    slur_start = True
                    import uuid
                    slur_id = f"slur_{uuid.uuid4().hex}"
                    spanned_notes = spanner.getSpannedElements()
                    slur_duration = sum(n.quarterLength for n in spanned_notes)
                    
                if spanner.isLast(m21_note):
                    slur_stop = True

        type_map = {
            'whole': 4.0,
            'half': 2.0,
            'quarter': 1.0,
            'eighth': 0.5,
            '16th': 0.25,
            '32nd': 0.125,
            '64th': 0.0625
        }
        base_dur = type_map.get(m21_note.duration.type, m21_note.quarterLength)
        
        return Note(
            pitch=pitch_name,
            duration=base_dur,
            accidental=accidental,
            dot=dot,
            tie_start=tie_start,
            tie_stop=tie_stop,
            tie_id=tie_id,
            tie_duration=tie_duration,
            slur_id=slur_id,
            slur_duration=slur_duration,
            offset=offset,
            id=m21_note.id
        )

    def _convert_chord(self, m21_chord: music21.chord.Chord, offset: float = 0.0) -> Note:
        # Extract pitches
        pitches = []
        for p in m21_chord.pitches:
            pitches.append(p.nameWithOctave.replace('-', 'b'))
            
        # Duration
        duration = m21_chord.quarterLength
        
        # Dot
        dot = m21_chord.duration.dots > 0
        
        # Ties (check chord tie)
        tie_start = False
        tie_stop = False
        tie_id = None
        tie_duration = 0.0
        
        if m21_chord.tie:
            if m21_chord.tie.type == 'start':
                tie_start = True
                import uuid
                tie_id = f"tie_{uuid.uuid4().hex}"
                tie_duration = m21_chord.quarterLength
            elif m21_chord.tie.type == 'stop':
                tie_stop = True
                
        # Slurs
        slur_start = False
        slur_stop = False
        slur_id = None
        slur_duration = 0.0
        
        spanners = m21_chord.getSpannerSites()
        for spanner in spanners:
            if isinstance(spanner, music21.spanner.Slur):
                if spanner.isFirst(m21_chord):
                    slur_start = True
                    import uuid
                    slur_id = f"slur_{uuid.uuid4().hex}"
                    spanned_notes = spanner.getSpannedElements()
                    slur_duration = sum(n.quarterLength for n in spanned_notes)
                    
                if spanner.isLast(m21_chord):
                    slur_stop = True

        type_map = {
            'whole': 4.0,
            'half': 2.0,
            'quarter': 1.0,
            'eighth': 0.5,
            '16th': 0.25,
            '32nd': 0.125,
            '64th': 0.0625
        }
        base_dur = type_map.get(m21_chord.duration.type, m21_chord.quarterLength)
        
        return Note(
            pitch=pitches,
            duration=base_dur,
            dot=dot,
            tie_start=tie_start,
            tie_stop=tie_stop,
            tie_id=tie_id,
            tie_duration=tie_duration,
            slur_id=slur_id,
            slur_duration=slur_duration,
            offset=offset,
            id=m21_chord.id
        )

    def _convert_rest(self, m21_rest: music21.note.Rest, offset: float = 0.0) -> Rest:
        dot = m21_rest.duration.dots > 0
        
        type_map = {
            'whole': 4.0,
            'half': 2.0,
            'quarter': 1.0,
            'eighth': 0.5,
            '16th': 0.25,
            '32nd': 0.125,
            '64th': 0.0625
        }
        base_dur = type_map.get(m21_rest.duration.type, m21_rest.quarterLength)
        
        return Rest(
            duration=base_dur,
            dot=dot,
            offset=offset,
            id=m21_rest.id
        )
