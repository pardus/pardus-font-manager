#!/usr/bin/env python3

# A simple font viewer that allows users to preview a font's style on their 
# system without permanently installing it.

import os
import gi
import sys
import shutil
import subprocess

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, Gdk, GLib
import font_charmaps
from ctypes import CDLL


class SimpleApp(Gtk.Window):
    def __init__(self, font_path=None):
        Gtk.Window.__init__(self, title="Simple Font Viewer")
        self.set_position(Gtk.WindowPosition.CENTER)

        self.set_default_size(600, 500)
        self.connect("destroy", Gtk.main_quit)

        self.libfontadder = CDLL("/usr/share/pardus/pardus-font-manager/src/libfontadder.so")


        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        self.label1 = Gtk.Label(label="Font Name")
        self.label2 = Gtk.Label(label=font_path if font_path else "No font path provided.")
        self.label3 = Gtk.Label(label="SAMPLE TEXT")

        vbox.pack_start(self.label1, True, True, 0)
        vbox.pack_start(self.label2, True, True, 0)
        vbox.pack_start(self.label3, True, True, 0)


        font_family, font_style = font_charmaps.get_font_name_from_file(font_path)
        font_name = f"{font_family} {font_style}"

        print("font name = ", font_name)
        self.label1.set_text(font_name)

        os.makedirs(os.path.expanduser("/tmp/.fonts"), exist_ok=True)
        shutil.copy2(font_path, os.path.expanduser("/tmp/.fonts"))

        copied_font_path = os.path.join(os.path.expanduser("/tmp/.fonts"), os.path.basename(font_path))
        if os.path.exists(copied_font_path):
            print(f"Font {copied_font_path} was successfully copied.")
        else:
            print(f"Failed to copy font to {copied_font_path}.")

        result = subprocess.run(["fc-cache", "-fv", "/tmp/.fonts/"], capture_output=True, text=True)
        print(result.stdout)

        result = self.libfontadder.fontmain(copied_font_path.encode('utf-8'))
        result = subprocess.run(["fc-cache", "-fv", "/tmp/.fonts/"], capture_output=True)

        if os.path.isfile(copied_font_path):
            font_family, font_style = font_charmaps.get_font_name_from_file(copied_font_path)
            if font_family and font_style:
                font_name = f"{font_family} {font_style}"

                self.font_description = Pango.FontDescription.from_string(font_name)
                self.label3.queue_draw()
                self.label3.override_font(self.font_description)
            else:
                print("Font metadata could not be retrieved!")
        else:
            print(f"File not found: {copied_font_path}")


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

    win = SimpleApp(font_path)
    win.show_all()
    Gtk.main()
