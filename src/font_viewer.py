#!/usr/bin/env python3

# A simple font viewer that allows users to preview a font's style on their 
# system without permanently installing it.

# To RUN:   ./font_viewer.py --details /path/to/font/file
#           ./Main.py --details /path/to/font/file

import os
import gi
import sys
import shutil
import subprocess

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, Gdk, GLib
import font_charmaps
from ctypes import CDLL


class FontViewer(Gtk.Window):
    def __init__(self, font_path=None):
        Gtk.Window.__init__(self, title="Pardus Font Viewer")
        self.set_position(Gtk.WindowPosition.CENTER)

        self.set_default_size(800, 600)
        self.connect("destroy", Gtk.main_quit)
        self.connect("destroy", self.cleanup)

        # self.libfontadder = CDLL("/usr/share/pardus/pardus-font-manager/src/libfontadder.so")
        self.libfontadder = CDLL(os.path.join(os.getcwd(), "libfontadder.so"))

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        self.font_name_label = Gtk.Label(label="Font Name")
        self.font_charmaps_label = Gtk.Label(
            label=font_path if font_path else "No font path provided."
        )
        self.font_charmaps_label.set_line_wrap(True)
        self.sample_label = Gtk.Label(label="SAMPLE TEXT")

        # Create a ScrolledWindow to contain the font_charmaps_label
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.font_charmaps_label)

        vbox.pack_start(self.font_name_label, True, True, 0)
        vbox.pack_start(scrolled_window, True, True, 0)
        vbox.pack_start(self.sample_label, True, True, 0)

        self.font_path = font_path

        font_family, font_style = font_charmaps.get_font_name_from_file(font_path)
        font_name = f"{font_family} {font_style}"

        print("font name = ", font_name)
        self.font_name_label.set_text(font_name)

        os.makedirs(os.path.expanduser("/tmp/.fonts"), exist_ok=True)
        shutil.copy2(font_path, os.path.expanduser("/tmp/.fonts"))

        copied_font_path = os.path.join(
            os.path.expanduser("/tmp/.fonts"), os.path.basename(font_path)
        )
        if os.path.exists(copied_font_path):
            print(f"Font {copied_font_path} was successfully copied.")
        else:
            print(f"Failed to copy font to {copied_font_path}.")

        result = self.libfontadder.fontmain(copied_font_path.encode('utf-8'))
        result = subprocess.run(
            ["fc-cache", "-fv", "/tmp/.fonts/"], capture_output=True, text=True
        )

        print(result.stdout)

        if os.path.isfile(copied_font_path):
            font_family, font_style = font_charmaps.get_font_name_from_file(copied_font_path)
            if font_family and font_style:
                font_name = f"{font_family} {font_style}"
                self.font_description = Pango.FontDescription.from_string(font_name)
                self.sample_label.queue_draw()
                self.sample_label.override_font(self.font_description)
                self.font_name_label.override_font(self.font_description)

                charmap_view = font_charmaps.get_font_charmaps(copied_font_path)
                if charmap_view:
                    # Take first key and key's value
                    font_name, (char_list, char_count) = list(charmap_view.items())[0]
                    # Convert char list to string format
                    char_str = '  '.join(char_list)
                    # Set the string to label for font charmap
                    self.font_charmaps_label.override_font(self.font_description)
                    self.font_charmaps_label.set_text(char_str)
            else:
                print("Font metadata could not be retrieved!")
        else:
            print(f"File not found: {copied_font_path}")


    def cleanup(self, widget):
        try:
            # Removing the font from /tmp/.fonts directory
            copied_font_path = os.path.join(
                os.path.expanduser("/tmp/.fonts"), os.path.basename(self.font_path)
            )
            if os.path.exists(copied_font_path):
                os.remove(copied_font_path)
                print(f"Font {copied_font_path} was successfully removed.")
            else:
                print(f"Font {copied_font_path} not found for removal.")
        except Exception as e:
            print(f"Error while cleaning up: {e}")


if __name__ == "__main__":
    # --details font/path
    font_path = None

    if "--details" in sys.argv:
        try:
            # index = sys.argv.index("--details")
            font_path = sys.argv[2] # index + 1
        except IndexError:
            pass

    os.environ["XDG_CONFIG_HOME"]= os.path.dirname(os.path.abspath(__file__))

    win = FontViewer(font_path)
    win.show_all()
    Gtk.main()