#!/usr/bin/env python3

import sys
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib
from MainWindow import MainWindow
from font_viewer import FontViewer

class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
            application_id="tr.org.pardus.font-manager",
            flags=Gio.ApplicationFlags(8),
            **kwargs)
        self.window = None
        self.args = None
        GLib.set_prgname("tr.org.pardus.font-manager")

        self.add_main_option(
            "details",
            ord("d"),
            GLib.OptionFlags(0),
            GLib.OptionArg(1),
            "Details page of font",
            None,
        )

    # The method that gets executed when the application is activated
    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            self.window = MainWindow(self)
        else:
            self.window.controlArgs()
        self.window.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()

        self.args = options

        if 'details' in options:
            font_path = options['details']
            if font_path:
                font_viewer = FontViewer(font_path)
                font_viewer.show_all()
                Gtk.main()
        else:
            self.activate()
        return 0

app = Application()
app.run(sys.argv)
