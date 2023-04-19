import os
import subprocess
from fontTools.ttLib import TTFont


def get_font_paths():
    """
    Try to get the font paths using `fc-list`, and return them as a set.
    If `fc-list` fails, use a default set of font paths.

    Returns:
        A set of font paths.
    """
    try:
        # Get font file paths from `fc-list` command output and convert to set
        font_output = subprocess.check_output(['fc-list', ':', '-f', '%{file}\n'])
        font_paths = set(os.path.dirname(line.strip().decode('utf-8')) for line in font_output.split(b'\n') if line.strip())
    except subprocess.CalledProcessError:
        # If `fc-list` fails, use default font paths
        font_paths = ['/usr/share/fonts', '/usr/local/share/fonts', os.path.expanduser('~/.fonts')]

    return font_paths


def get_font_charmaps(font_file_path):
    """
    Load a font file using `TTFont`, extract its name and character maps, and return them as a dictionary.
    If loading the font file fails, return an empty dictionary.

    Args:
        font_file_path (str): path to the font file.

    Returns:
        A dictionary containing the font name as the key and a list of characters as the value.
    """
    try:
        with TTFont(font_file_path) as font:
            charmap = font.getBestCmap()
            font_name = font['name'].getName(1, 3, 1, 1033).toUnicode()
            char_list = [chr(code) for code in charmap.keys()]
            return {font_name: char_list}
    except Exception as e:
        print(f'Error: failed to load font file "{font_file_path}": {e}')
        return {}


def get_fonts_charmaps():
    """
    Generate a dictionary of font names and their character maps by looping over
    the font files in each font path obtained using get_font_paths. For each
    font file, call get_font_charmaps to get its name and character maps, and
    add them to the dictionary using the font name as the key.

    Returns:
        A dictionary of font names and their character maps.
    """
    font_charmaps = {}
    font_paths = get_font_paths()
    for font_path in font_paths:
        # Generate an iterator of font file names in the given font directory path,
        # filtered to include only files with '.ttf' or '.otf' extensions.
        font_files = (f for f in os.listdir(font_path) if any(f.endswith(extension) for extension in ('.ttf', '.otf')))
        for filename in font_files:
            font_file_path = os.path.join(font_path, filename)
            charmaps = get_font_charmaps(font_file_path)
            user_added = font_file_path.startswith('/home')
            charmaps.update({font_name: (char_list, user_added)
                              for font_name, char_list in charmaps.items()})
            font_charmaps.update(charmaps)
    return font_charmaps
