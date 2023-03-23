import os
import subprocess
from fontTools.ttLib import TTFont


def get_font_paths():
    """
    Try to get the font paths using `fc-list`, and return them as a set.
    If `fc-list` fails, use a default set of font paths.
    """
    try:
        font_output = subprocess.check_output(['fc-list', ':', '-f', '%{file}\n'])
        font_paths = set(os.path.dirname(line.strip().decode('utf-8')) for line in font_output.split(b'\n') if line.strip())
    except subprocess.CalledProcessError:
        font_paths = ['/usr/share/fonts', '/usr/local/share/fonts', os.path.expanduser('~/.fonts')]
    return font_paths


def get_font_charmaps(font_file_path):
    """
    Load a font file using `TTFont` and return its name and character maps as a tuple.
    If loading the font file fails, return an empty tuple.
    """
    try:
        font = TTFont(font_file_path)
    except Exception as e:
        print(f'Error: failed to load font file "{font_file_path}": {e}')
        return {}
    charmap = font.getBestCmap()
    font_name = font['name'].getName(1, 3, 1, 1033).toUnicode()
    char_list = [chr(code) for code in charmap.keys()]
    font.close()
    return {font_name: char_list}


def get_fonts_charmaps():
    """
    Get the font paths using `get_font_paths`, and loop over all the font files
    in each path. For each font file, call `get_font_charmaps` to get its name
    and character maps, and add them to a dictionary using the font name as the key.
    """
    font_charmaps = {}
    font_paths = get_font_paths()
    for font_path in font_paths:
        for filename in os.listdir(font_path):
            if not (filename.endswith('.ttf') or filename.endswith('.otf')):
                continue
            font_file_path = os.path.join(font_path, filename)
            charmaps = get_font_charmaps(font_file_path)
            if charmaps:
                font_charmaps.update(charmaps)
    return font_charmaps
