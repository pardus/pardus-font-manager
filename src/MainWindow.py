import os
import string

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Pango, PangoCairo


keys = [key for key in list(string.printable)
 if key not in [' ', '\t', '\n', '\r', '\x0b', '\x0c']]

# keys = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 
#         'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',\
#         'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E',\
#         'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',\
#         'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0',\
#         '1', '2', '3', '4', '5', '6', '7', '8', '9', '!','@',\
#         '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '-',\
#         '=', '[', ']', '{', '}', ';', ":", "'", '"', '\\', '|',\
#         ',', '.', '<', '>', '/', '?', '`', '~']

class MainWindow:

    def __init__(self, app):

        self.builder = Gtk.Builder()

        glade_file = os.path.join("..", "ui", "fm-ui.glade")
        self.builder.add_from_file(glade_file)


        # Connect the signals defined in the Glade file to the methods in this class 
        self.builder.connect_signals(self)

        # Get the window object from the Glade file
        self.window = self.builder.get_object("window")
        self.window.set_title("Pardus Font Manager")
        self.window.set_default_size(800, 600)

        # Get objects from the Glade file
        self.grid = self.builder.get_object("right_grid")
        top_box = self.builder.get_object("top_box")
        vbox = self.builder.get_object("vbox")
        hbox = self.builder.get_object("hbox")

        self.fonts_list = Gtk.ListStore(str)  # Create a list to store the fonts
        self.update_fonts_list()  # Populate the list with the currently installed fonts

        self.fonts_view = Gtk.TreeView(model=self.fonts_list)  # Create a TreeView to display the list of fonts
        self.fonts_view.set_headers_visible(False)
        self.fonts_view.append_column(Gtk.TreeViewColumn("Fonts", Gtk.CellRendererText(), text=0))
        self.fonts_view.get_selection().connect("changed", self.on_font_selected)

        self.label = self.builder.get_object("label1")
        self.label.set_size_request(50, 60)
        top_box.pack_start(self.label, True, True, 0)

        # Add a scrolled window
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.fonts_view)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        hbox.pack_start(scrolled_window, True, True, 0)

        # Loop through the keys and create labels for each one 
        for i, key in enumerate(keys):
            label = Gtk.Label(label=key)
            # Add the button to the grid, with a width of 1 and a height of 1
            self.grid.attach(label, i % 7, i // 7, 2, 2)

        # Set the application for the window to the Gtk.Application passed from the main file
        self.window.set_application(app) 

        # Show the window and all of its widgets 
        self.window.show_all()

    def on_font_selected(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            font_name = model[treeiter][0]
            font_description = Pango.FontDescription.from_string(font_name)
            self.label.override_font(font_description)
            self.label.set_text("The quick brown fox jumps over the lazy dog.")

            for i, key in enumerate(keys):
                label = self.grid.get_child_at(i % 7, i // 7)
                label.override_font(font_description)

    def update_fonts_list(self):
        font_map = PangoCairo.font_map_get_default()  # Get the default font map
        context = font_map.create_context()  # Create a font context
        families = context.list_families()  # Get a list of available font families
        self.fonts_list.clear()
        for family in families:
            self.fonts_list.append([family.get_name()])  # Add the name of each font family to the list
