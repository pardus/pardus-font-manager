#!/usr/bin/env python3

import sys
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, Gio

from MainWindow import MainWindow

class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
            application_id="tr.org.pardus.font-manager",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
            **kwargs)
    
    # The method that gets executed when the application is activated
    def do_activate(self):
        # Create an instance of the MainWindow class and assign it to the window attribute
        self.window = MainWindow(self)

# Create an instance of the Application class
app = Application()
# Run the application and pass in the command line arguments
app.run(sys.argv)
