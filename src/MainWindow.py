import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

from font_charmaps import get_fonts_charmaps


font_charmaps = get_fonts_charmaps()


class MainWindow:

    def __init__(self, app):

        # Create the builder and load the Glade file
        self.builder = Gtk.Builder()
        glade_file = os.path.join("..", "ui", "fm-ui.glade")
        self.builder.add_from_file(glade_file)

        # Connect signals from the Glade file to the methods in this class
        self.builder.connect_signals(self)

        # Get window and set properties
        self.window = self.builder.get_object("window")
        self.window.set_border_width(10)

        # Get widgets from the Glade file
        top_box = self.builder.get_object("top_box")
        vbox = self.builder.get_object("vbox")
        hbox = self.builder.get_object("hbox")
        left_scrolled = self.builder.get_object("left_scrolled")
        self.search_entry = self.builder.get_object("search_entry")
        self.stack_start = self.builder.get_object("stack_start")
        self.stack_map = self.builder.get_object("stack_map")
        self.page_start = self.builder.get_object("page_start")
        self.page_list = self.builder.get_object("page_list")
        self.spinner_start = self.builder.get_object("spinner_start")
        self.spinner_charmaps = self.builder.get_object("spinner_charmaps")
        self.add_button = self.builder.get_object("add_button")
        self.try_button = self.builder.get_object("try_button")
        self.info_button = self.builder.get_object("info_button")
        self.charmaps_lbl = self.builder.get_object("charmaps_lbl")
        self.label = self.builder.get_object("label1")

        self.info_button.set_visible(False)

        # Connect signals to widget methods
        self.search_entry.connect("changed", self.on_search_entry_changed)
        self.add_button.connect("clicked", self.on_add_button_clicked)
        self.try_button.connect("clicked", self.on_try_button_clicked)
        self.info_button.connect("clicked", self.on_info_button_clicked)

        # Create and populate the fonts list
        self.fonts_list = Gtk.ListStore(str)
        self.update_fonts_list()

        # Create and set up the TreeView for the fonts list
        self.fonts_view = Gtk.TreeView(model=self.fonts_list)
        self.fonts_view.set_headers_visible(False)
        self.fonts_view.append_column(Gtk.TreeViewColumn("Fonts", Gtk.CellRendererText(), text=0))
        self.fonts_view.get_selection().connect("changed", self.on_font_selected)

        # Add a scrolled window for the fonts list
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.fonts_view)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        left_scrolled.pack_start(scrolled_window, True, True, 0)

        # Set window properties
        self.window.set_title("Pardus Font Manager")
        self.window.set_default_size(800, 600)
        self.window.set_application(app)
        self.window.show_all()


    def on_search_entry_changed(self, search_entry):
            """
            This function is called every time the search entry is changed.
            It retrieves the current search text from the search entry widget,
            filters the font list based on the search text, clears the current list of fonts,
            and populates the list with the filtered fonts.
            """
            search_text = search_entry.get_text().lower()

            # If the search box is empty, show all fonts
            if not search_text:
                self.update_fonts_list()
                return

            # Filter the font list by matching the search string with the font names
            filtered_fonts = [(font_name, charmaps) for font_name,
                              charmaps in font_charmaps.items() if search_text in font_name.lower()]

            # Clear the current list of fonts
            self.fonts_list.clear()

            # Populate the list with the filtered fonts
            for font_name, charmaps in filtered_fonts:
                iter = self.fonts_list.append([font_name])
                self.fonts_list.set(iter, 0, font_name)


    def on_font_selected(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            font_name = model[treeiter][0]
            print("Selected Font ---> ", font_name)
            font_description = Pango.FontDescription.from_string(font_name)
            self.label.override_font(font_description)
            self.label.set_text("The quick brown fox jumps over the lazy dog.")

            font_charmap = font_charmaps[font_name] # Get the charmap for the selected font

            def get_remaining_elements(lst):
                """
                This function takes a list of strings as input and returns a new list
                containing all the elements from the input list starting from the first
                element that doesn't start with any whitespace or carriage return characters ('\r', ' '),
                and skipping any elements that start with the same character(s)
                as the first non-whitespace element.
                """
                first_element = [e for e in lst[0] if e not in ('\r', ' ')]
                remaining_elements = []
                for i in range(1, len(lst)):
                    if lst[i][0] in first_element:
                        continue
                    else:
                        remaining_elements = lst[i:]
                        break
                return remaining_elements

            # Gives more info about selected font
            self.info_button.set_visible(True)

            # This section was added due to the problem of listing charmaps of fonts that
            # contain spaces or similar characters in charmaps in charmaps
            font_charmap_without_gap = get_remaining_elements(font_charmap)
            font_charmap_string = '   '.join([char for char in font_charmap_without_gap if char != ' '])

            self.charmaps_lbl.override_font(font_description)
            self.charmaps_lbl.set_text(font_charmap_string)


    # + Call after adding new fonts, del unnecassary parts
    def update_fonts_list(self):
        for font_name, charmaps in font_charmaps.items():
            iter = self.fonts_list.append([font_name])
            # Set the font name in the row identified by the iter
            self.fonts_list.set(iter, 0, font_name)


    def on_add_button_clicked(self, button):
        pass

    def on_try_button_clicked(self, button):
        pass

    def on_info_button_clicked(self, button):
        pass
