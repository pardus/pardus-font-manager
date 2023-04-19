import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, Gdk, GLib
import subprocess
import shutil
from fontTools.ttLib import TTFont
from font_charmaps import get_fonts_charmaps


font_charmaps = get_fonts_charmaps()


class MainWindow:

    def __init__(self, app):

        # Create the builder and load the Glade file
        self.builder = Gtk.Builder()
        glade_file = os.path.dirname(os.path.abspath(__file__)) + "/../ui/fm-ui.glade"

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
        self.entry = self.builder.get_object("entry")
        self.stack_start = self.builder.get_object("stack_start")
        self.stack_map = self.builder.get_object("stack_map")
        self.page_start = self.builder.get_object("page_start")
        self.page_list = self.builder.get_object("page_list")
        self.spinner_start = self.builder.get_object("spinner_start")
        self.spinner_charmaps = self.builder.get_object("spinner_charmaps")
        self.add_button = self.builder.get_object("add_button")
        self.try_button = self.builder.get_object("try_button")
        self.info_button = self.builder.get_object("info_button")
        self.charmaps_label = self.builder.get_object("charmaps_label")
        self.label = self.builder.get_object("label1")
        self.font_name_label = self.builder.get_object("font_name_label")
        self.font_size_label = self.builder.get_object("font_size_label")
        self.font_color_label = self.builder.get_object("font_color_label")
        self.ok_button = self.builder.get_object("ok_button")
        self.cancel_button = self.builder.get_object("cancel_button")
        self.info_dialog = self.builder.get_object("info_dialog")
        self.color_button = self.builder.get_object("color_button")
        self.spin_button = self.builder.get_object("spin_button")
        self.remove_button = self.builder.get_object("remove_button")

        # Connect signals to widget methods
        self.search_entry.connect("changed", self.on_search_entry_changed)
        self.add_button.connect("clicked", self.on_add_button_clicked)
        self.try_button.connect("clicked", self.on_try_button_clicked)
        self.info_button.connect("clicked", self.on_info_button_clicked)
        self.remove_button.connect("clicked", self.on_remove_button_clicked)

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

        self.window.show_all()
        self.info_button.set_visible(False)
        self.remove_button.set_visible(False)
        self.font_description = None

        # Set window properties
        self.window.set_title("Pardus Font Manager")
        self.window.set_default_size(800, 600)
        self.window.set_application(app)


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
        """
        This function handles the selection of a font by the user.
        It gets the selected font from the font selection dialog,
        sets the font description of the label to the selected font,
        and displays the character map of the font.
        """
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            font_name = model[treeiter][0]
            self.font_description = Pango.FontDescription.from_string(font_name)

            # Show the remove button only for the fonts that have been added by the user
            _, user_added = font_charmaps[font_name]
            self.remove_button.set_visible(user_added)

            self.label.override_font(self.font_description)
            self.label.set_text("The quick brown fox jumps over the lazy dog.")

            # Get the charmap and user_added flag for the selected font
            font_charmap, user_added = font_charmaps[font_name]

            # Gives more info about selected font
            self.info_button.set_visible(True)

            font_charmap_string = '   '.join([char for char in font_charmap if char.isprintable()])
            self.charmaps_label.override_font(self.font_description)
            self.charmaps_label.set_text(font_charmap_string)


    def update_fonts_list(self):
        # Get a list of font names sorted alphabetically
        font_names = sorted(list(font_charmaps.keys()))

        # Populate the list store with the sorted font names
        self.fonts_list.clear()
        for font_name in font_names:
            self.fonts_list.append([font_name])


    def on_add_button_clicked(self, button):
        """
        This function allows the user to select a font file,
        copies the font file to the user's font directory,
        updates the font cache, and reads the charmaps for the new font.
        Then it adds the font and its charmaps to a dictionary and
        updates font list in the UI.
        """
        dialog = Gtk.FileChooserDialog(
            "Please choose a font file", self.window, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        filter_ttf = Gtk.FileFilter()
        filter_ttf.set_name("TTF files")
        filter_ttf.add_mime_type("application/x-font-ttf")
        dialog.add_filter(filter_ttf)

        filter_otf = Gtk.FileFilter()
        filter_otf.set_name("OTF files")
        filter_otf.add_mime_type("application/x-font-otf")
        dialog.add_filter(filter_otf)

        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            dialog.destroy()
            return

        try:
            filepath = dialog.get_filename()

            # Create the .fonts directory if it doesn't exist
            os.makedirs(os.path.expanduser("~/.fonts"), exist_ok=True)

            # Copy the font file to ~/.fonts
            shutil.copy2(filepath, os.path.expanduser("~/.fonts"))

            # Update the font cache
            subprocess.run(["fc-cache", "-f", "-v"], capture_output=True)
            subprocess.run(["fc-cache", "-f", "-v", "-r"], capture_output=True)

            # Read the charmaps for the new font
            font_charmap = []
            with open(filepath, 'rb') as f:
                ttfont = TTFont(f)
                for cmap in ttfont['cmap'].tables:
                    if cmap.isUnicode():
                        font_charmap.extend(chr(k) for k in cmap.cmap.keys())

            # Add the font and its charmaps to the dictionary
            font_filename = os.path.basename(filepath)
            font_name, _ = os.path.splitext(font_filename)
            font_charmaps[font_name] = (font_charmap, True)  # Set user_added to True


            self.update_fonts_list()  # Change: Update the UI to show the new font in the list

        except Exception as e:
            print(f"An error occurred: {e}")

        dialog.destroy()


    def on_try_button_clicked(self, button):
        if self.font_description is None:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text="No font selected",
            )
            dialog.format_secondary_text(
                "Please choose a font from the list before trying again."
            )
            dialog.run()
            dialog.destroy()
        else:
            text = self.entry.get_text()
            self.label.override_font(self.font_description)
            self.label.set_text(text)


    def on_info_button_clicked(self, button):
        """
        This function is called when the info button is clicked.
        It creates a new dialog with a font size spin button.
        """
        # self.info_dialog.set_title("Font Info")
        # self.info_dialog.run()
        # self.info_dialog.hide()

        dialog = Gtk.Dialog(title="Font Info", parent=self.window, flags=0)
        dialog.set_default_size(300, 300)
        dialog.set_modal(True)

        # Create the spin button for font size
        font_size_label = Gtk.Label("Font Size:")
        font_size_spin_button = Gtk.SpinButton.new_with_range(8, 96, 2)
        font_size_spin_button.set_value(int(self.font_description.get_size() / Pango.SCALE))

        # Add the font size spin button to the dialog
        dialog_box = dialog.get_content_area()
        dialog_box.add(font_size_label)
        dialog_box.add(font_size_spin_button)

        # Add an "OK" button to the dialog box
        ok_button = dialog.add_button("OK", Gtk.ResponseType.OK)

        # Add a "Cancel" button to the dialog box
        cancel_button = dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)

        # Show the dialog
        dialog.show_all()


        # Connect the response signal to update the font description and label
        def on_response(dialog, response_id):
            if response_id == Gtk.ResponseType.OK:
                # Update the font size
                font_size = font_size_spin_button.get_value_as_int()

                self.font_description.set_size(font_size * Pango.SCALE)
                self.label.override_font(self.font_description)
                self.label.set_text("The quick brown fox jumps over the lazy dog.")

            dialog.destroy()

        dialog.connect("response", on_response)


    def delete_font_file(self, font_name):
        try:
            # Execute fc-list command to list fonts with the given name
            output = subprocess.check_output(["fc-list", font_name, "-f", "%{file}\n"], universal_newlines=True)
            # Split the output by newline to get a list of font file paths
            font_files = output.strip().split("\n")
            if font_files:
                # Return the first font file path
                return font_files[0]
            else:
                print("Font not found.")
        except subprocess.CalledProcessError:
            # Error occurred while executing fc-list command
            print("Error: Failed to list fonts.")
        return None


    def delete_font(self, font_name):
        font_file = self.delete_font_file(font_name)
        if font_file:
            # Extract the folder path from the font file path
            font_folder = os.path.dirname(font_file)
            # Delete the font file
            os.remove(font_file)
            print(f"Deleted font file: {font_file}")
            # Delete the parent directory if it is empty
            if not os.listdir(font_folder):
                os.rmdir(font_folder)
                print(f"Deleted empty folder: {font_folder}")


    def on_remove_button_clicked(self, button):
        """
        It removes the selected font from the user_fonts dictionary,
        updates the fonts list, and saves the updated user_fonts dictionary.
        """
        # Get the selected font from the TreeView
        selection = self.fonts_view.get_selection()
        model, iter_ = selection.get_selected()
        if iter_:
            font_name = model[iter_][0]

            # Remove the font from the font_charmaps dictionary
            del font_charmaps[font_name]
            self.delete_font(font_name)

            # Update the fonts list in the TreeView
            self.update_fonts_list()
