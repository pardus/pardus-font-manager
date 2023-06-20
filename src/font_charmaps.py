import os
import subprocess
import re


def get_font_paths():
    """
    Try to get the font file paths using `fc-list`, and return them as a set.
    If `fc-list` fails, use a default set of font paths.

    Returns:
        A set of file paths.
    """
    try:
        font_output = subprocess.check_output(['fc-list', ':', '-f', '%{file}\n'])
        font_files = {line.strip().decode('utf-8')
                      for line in font_output.split(b'\n') if line.strip()}
    except subprocess.CalledProcessError:
        font_files = set()
    return font_files


def get_font_names():
    """
    Retrieve the list of all font names installed on the system.

    Returns:
        list: A list of string where each string represents a font name.
    """
    fonts = subprocess.run(['fc-list', '--format=%{family[0]}\n'],
                            stdout=subprocess.PIPE, text=True)
    fonts = fonts.stdout.split('\n')
    return [font for font in fonts if font]


def get_font_charmaps(font_file_path):
    """
    Extract font's character maps using `fc-query`, and return them as a
    dictionary. If loading the font file fails, return an empty dictionary.

    Args:
        font_file_path (str): path to the font file.

    Returns:
        dict: A dictionary where the font name is the key and the character maps
        are the value.
    """
    try:
        result = subprocess.run(['fc-query', '--format=%{family[0]}: %{charset}\n',
                                 font_file_path],
                                 stdout=subprocess.PIPE, text=True)
        output = result.stdout.split(':', 1)
        if len(output) < 2:
            raise Exception('Failed to extract font name and charmap')
        font_name = output[0].strip()
        charmap_raw = output[1]

        charmap = []
        for range_str in re.findall(r'([0-9a-fA-F]+)-?([0-9a-fA-F]+)?',
                                    charmap_raw):
            start, end = range_str
            start = int(start, 16)
            end = int(end, 16) if end else start
            for i in range(start, min(end, 0x110000) + 1):
                charmap.append(chr(i))

        charmap_count = len(charmap)
        return {font_name: (charmap, charmap_count)}

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
    for font_file_path in font_paths:
        if os.path.isfile(font_file_path) and font_file_path.endswith(('.ttf', '.otf')):
            charmaps = get_font_charmaps(font_file_path)
            user_added = font_file_path.startswith(os.path.expanduser("~"))
            charmaps.update({font_name: (char_list, charmap_count, user_added)
                              for font_name, (char_list, charmap_count)
                                in charmaps.items()})
            font_charmaps.update(charmaps)
    return font_charmaps


def get_font_file_path(font_name):
    """
    Retrieve the file path of the specified font name.

    Args:
        font_name (str): The name of the font to retrieve the file path for.

    Returns:
        str: The file path of the font, or None if an error occurred.
    """
    try:
        result = subprocess.run(['fc-match', '--format=%{file}', font_name],
                                 capture_output=True, text=True)
        font_file_path = result.stdout.strip()
        return font_file_path
    except Exception as e:
        print(f"Error: Failed to get font file path for '{font_name}': {str(e)}")
        return None


def get_selected_font_charmaps(font_name):
    """
    Get the character map for the specified font name.

    Args:
        font_name (str): The name of the font to get the character map for.

    Returns:
        dict: A dictionary containing character map information for the
        specified font, or an empty dictionary if the font was not found.
    """
    font_file_path = get_font_file_path(font_name)
    if font_file_path:
        font_charmaps = get_font_charmaps(font_file_path)
        user_added = font_file_path.startswith(os.path.expanduser("~"))
        for font_name, (char_list, charmap_count) in font_charmaps.items():
            font_charmaps[font_name] = (char_list, charmap_count, user_added)
        return {font_name: font_charmaps[font_name]}
    else:
        return {}
