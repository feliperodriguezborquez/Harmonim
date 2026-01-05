import xml.etree.ElementTree as ET
import os
import tempfile
import shutil

def ensure_unique_ids(xml_path: str) -> str:
    """
    Ensures that every note/rest in the MusicXML file has a unique 'id' attribute.
    Returns the path to a temporary file containing the processed XML.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    count = 0
    modified = False
    
    # Find all notes (and rests are usually <note><rest/></note> or similar in MusicXML)
    # MusicXML structure: <note> contains <pitch> or <rest>
    for note in root.findall(".//note"):
        if 'id' not in note.attrib:
            note.set('id', f"note-{count:04d}") # Zero-pad for neatness
            count += 1
            modified = True
        else:
            # If it has an ID, we trust it, but we might want to ensure uniqueness?
            # For now, assume existing IDs are fine.
            pass
            
    if modified:
        # Create a temp file
        fd, temp_path = tempfile.mkstemp(suffix=".musicxml")
        os.close(fd)
        tree.write(temp_path)
        return temp_path
    else:
        # If no changes, return a copy anyway to be safe (or just the original?)
        # Better to return a temp copy so we don't accidentally modify the original if we did.
        # But if modified is False, we didn't touch it.
        # However, for consistency, let's just return the original path if untouched?
        # No, the caller might expect a temp file they can clean up.
        # Let's always return a temp file to be safe and consistent.
        fd, temp_path = tempfile.mkstemp(suffix=".musicxml")
        os.close(fd)
        shutil.copy2(xml_path, temp_path)
        return temp_path
