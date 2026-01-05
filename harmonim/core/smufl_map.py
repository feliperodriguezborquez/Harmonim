"""
Mapping of musical symbols to SMuFL (Standard Music Font Layout) unicode characters.
Reference: https://w3c.github.io/smufl/latest/tables/
"""

SMUFL_MAP = {
    # Clefs
    'clef_g': '\uE050',      # G clef
    'clef_f': '\uE062',      # F clef
    'clef_c': '\uE05C',      # C clef

    # Noteheads
    'notehead_black': '\uE0A4',
    'notehead_half': '\uE0A3',
    'notehead_whole': '\uE0A2',
    'notehead_double_whole': '\uE0A0',

    # Accidentals
    'accidental_flat': '\uE260',
    'accidental_natural': '\uE261',
    'accidental_sharp': '\uE262',
    'accidental_double_sharp': '\uE263',
    'accidental_double_flat': '\uE264',

    # Rests
    'rest_whole': '\uE4E3',
    'rest_half': '\uE4E4',
    'rest_quarter': '\uE4E5',
    'rest_eighth': '\uE4E6',
    'rest_sixteenth': '\uE4E7',
    'rest_thirty_second': '\uE4E8',
    'rest_sixty_fourth': '\uE4E9',
    
    # Flags
    'flag_eighth_up': '\uE240',
    'flag_eighth_down': '\uE241',
    'flag_sixteenth_up': '\uE242',
    'flag_sixteenth_down': '\uE243',
    
    # Dynamics
    'dynamic_p': '\uE520',
    'dynamic_m': '\uE521',
    'dynamic_f': '\uE522',
    'dynamic_r': '\uE523',
    'dynamic_s': '\uE524',
    'dynamic_z': '\uE525',
    'dynamic_n': '\uE526',
    
    # Articulations
    'artic_accent': '\uE4A0',
    'artic_staccato': '\uE4A2',
    'artic_tenuto': '\uE4A4',
    'artic_marcato': '\uE4AC',

    # Time Signatures
    'time_sig_0': '\uE080',
    'time_sig_1': '\uE081',
    'time_sig_2': '\uE082',
    'time_sig_3': '\uE083',
    'time_sig_4': '\uE084',
    'time_sig_5': '\uE085',
    'time_sig_6': '\uE086',
    'time_sig_7': '\uE087',
    'time_sig_8': '\uE088',
    'time_sig_9': '\uE089',
    'time_sig_common': '\uE08A',
    'time_sig_cut': '\uE08B',
    
    # Brackets and Braces
    'brace': '\uE000',
    'bracket': '\uE002',
}

def get_smufl_char(name: str) -> str:
    """Get the SMuFL unicode character for a given symbol name."""
    return SMUFL_MAP.get(name, '')
