import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, Gdk, GLib
import subprocess
import shutil
import re
from font_charmaps import get_fonts_charmaps
import threading
from threading import Thread


class MainWindow:

    def __init__(self, app):
        # Glade file handling and builder setup
        self.builder = Gtk.Builder()
        glade_file = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # Window setup
        self.window = self.builder.get_object("window")
        self.window.set_border_width(10)

        # Font charmap setup and sample text
        self.font_charmaps = []
        self.sample_text = "The quick brown fox jumps over the lazy dog."

        # Widget extraction from Glade file
        # Top-level widgets
        top_box = self.builder.get_object("top_box")
        vbox = self.builder.get_object("vbox")
        hbox = self.builder.get_object("hbox")

        # Buttons and dialog
        self.menu_button = self.builder.get_object("menu_button")
        self.add_button = self.builder.get_object("add_button")
        self.try_button = self.builder.get_object("try_button")
        self.info_button = self.builder.get_object("info_button")
        self.ok_button = self.builder.get_object("ok_button")
        self.cancel_button = self.builder.get_object("cancel_button")
        self.info_dialog = self.builder.get_object("info_dialog")
        self.more_button = self.builder.get_object("more_button")

        # Label and entry widgets
        self.search_entry = self.builder.get_object("search_entry")
        self.entry = self.builder.get_object("entry")
        self.charmaps_label = self.builder.get_object("charmaps_label")
        self.label = self.builder.get_object("label_entry")
        self.font_name_label = self.builder.get_object("font_name_label")
        self.font_size_label = self.builder.get_object("font_size_label")
        self.font_color_label = self.builder.get_object("font_color_label")

        # Additional widgets
        self.left_scrolled = self.builder.get_object("left_scrolled")
        self.left_scrolled_box = self.builder.get_object("left_scrolled_box")
        self.right_scrolled = self.builder.get_object("right_scrolled")
        self.stack_start = self.builder.get_object("stack_start")
        self.stack_map = self.builder.get_object("stack_map")
        self.page_charmap = self.builder.get_object("page_charmap")
        self.page_list = self.builder.get_object("page_list")
        self.spinner_start = self.builder.get_object("spinner_start")
        self.color_button = self.builder.get_object("color_button")
        self.spin_button = self.builder.get_object("spin_button")
        self.size_spin_button = self.builder.get_object("size_spin_button")
        self.remove_button = self.builder.get_object("remove_button")
        self.increase_button = self.builder.get_object("increase_button")
        self.decrease_button = self.builder.get_object("decrease_button")
        self.title_box = self.builder.get_object("title_box")
        self.mlozturk = self.builder.get_object("mlozturk")
        self.fonts_view = self.builder.get_object("fonts_view")
        self.menu_popover = self.builder.get_object("menu_popover")
        self.menu_about = self.builder.get_object("menu_about")

        self.dialog_font_manager = self.builder.get_object("dialog_font_manager")
        self.dialog_font_manager.set_program_name(("Pardus Font Manager"))

        # Adjustment setup for size_spin_button
        adjustment = Gtk.Adjustment.new(12, 1, 96, 1, 10, 0)
        self.size_spin_button.set_adjustment(adjustment)

        # Start spinner
        self.spinner_start.start()

        # Signal connection for widgets
        self.search_entry.connect("changed", self.on_search_entry_changed)
        self.entry.connect("changed", self.update_sample_text)
        self.entry.connect("activate", self.update_sample_text)
        self.add_button.connect("clicked", self.on_add_button_clicked)
        self.info_button.connect("clicked", self.on_info_button_clicked)
        self.remove_button.connect("clicked", self.on_remove_button_clicked)
        self.increase_button.connect("clicked", self.on_increase_button_clicked)
        self.decrease_button.connect("clicked", self.on_decrease_button_clicked)
        self.menu_about.connect("clicked", self.on_menu_about_clicked)
        self.more_button.connect("clicked", self.on_more_button_clicked)

        # Signal connection for spin buttons
        self.size_spin_button.connect("value-changed", self.on_size_spin_button_value_changed)

        # Fonts list and TreeView setup
        self.fonts_list = Gtk.ListStore(str)
        self.fonts_view.set_headers_visible(False)
        self.fonts_view.set_model(self.fonts_list)
        self.fonts_view.append_column(Gtk.TreeViewColumn("Fonts", Gtk.CellRendererText(), text=0))
        self.fonts_view.get_selection().connect("changed", self.on_font_selected)
        self.fonts_view.connect("key-press-event", self.on_key_press_event)

        # Window display
        self.window.show_all()

        # Threading setup for worker function
        p1 = threading.Thread(target=self.worker)
        p1.daemon = True
        p1.start()

        # Button sensitivity and visibility setup
        self.menu_button.set_sensitive(False)
        self.info_button.set_sensitive(False)
        self.info_button.set_visible(False)
        self.remove_button.set_sensitive(False)
        self.more_button.set_visible(False)


        # Font description initialization
        self.font_description = None
        self.char_display_limit = 5000
        self.c_count = False

        # Window properties setup
        self.window.set_title("Pardus Font Manager")
        self.window.set_default_size(800, 600)
        self.window.set_application(app)


    def worker(self):
        # self.font_charmaps = get_fonts_charmaps()
        self.update_fonts_list()
        self.set_page()


    def set_page(self):
        GLib.idle_add(self.stack_start.set_visible_child_name, "page_list")
        GLib.idle_add(self.menu_button.set_sensitive, True)


    def loading_finished(self):
        self.spinner_start.stop()
        self.stack_start.set_visible_child_name("page_list")


    def on_size_spin_button_value_changed(self, spin_button):
        new_font_size = spin_button.get_value_as_int()
        self.update_sample_text_size(new_font_size)


    def update_sample_text_size(self, new_size):
        if self.font_description is not None:
            self.font_description.set_size(new_size * Pango.SCALE)
            self.label.override_font(self.font_description)
            self.label.set_text(self.entry.get_text() if self.entry.get_text().strip() != "" else self.sample_text)


    def on_menu_about_clicked(self, button):
        self.menu_popover.popdown()
        self.dialog_font_manager.run()
        self.dialog_font_manager.hide()


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
        filtered_fonts = [(font_name, charmaps) for font_name, (charmaps, _, _) in self.font_charmaps.items() if search_text in font_name.lower()]


        # Clear the current list of fonts
        self.fonts_list.clear()

        # Populate the list with the filtered fonts
        for font_name, charmaps in filtered_fonts:
            iter = self.fonts_list.append([font_name])
            self.fonts_list.set(iter, 0, font_name)


    def get_selected_font_info(self):
        """
        Get the font name and user_added status of the selected font.

        Returns:
            The font name as a string and user_added status as a boolean.
        """
        selection = self.fonts_view.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            font_name = model[treeiter][0]
            # Get the charmap, charmap count, and user_added flag for the selected font
            _, charmap_count, user_added = self.font_charmaps[font_name]
            # print(f"CHARMAP for '{font_name}' -------------")
            # print(self.font_charmaps[font_name])
            if charmap_count > self.char_display_limit:
                print(f"'{font_name}' includes {charmap_count - self.char_display_limit} more characters than what is shown.")
                self.more_button.set_visible(True)
                self.c_count = True
            else:
                self.more_button.set_visible(False)
                self.c_count = False

            return font_name, user_added, self.c_count
        return None, None, False


    def on_font_selected(self, selection):
        """
        This function handles the selection of a font by the user.
        It gets the selected font from the font selection dialog,
        sets the font description of the label to the selected font,
        displays the character map of the font, and shows a spinner
        while the character map is being displayed.
        """
        font_name, user_added, self.c_count = self.get_selected_font_info()
        # Reset the display limit
        self.char_display_limit = 5000
        if font_name is not None:
            self.font_description = Pango.FontDescription.from_string(font_name)

            # Show the remove button only for the fonts that have been added by the user
            self.remove_button.set_sensitive(user_added)

            self.label.override_font(self.font_description)
            self.label.set_text(self.entry.get_text() if self.entry.get_text().strip() != "" else self.sample_text)

            # Get the charmap, char_map_count and user_added flag for the selected font
            font_charmap, _, _ = self.font_charmaps[font_name]

            # Gives more info about selected font
            self.info_button.set_sensitive(True)

            # If the character count is more than char_display_limit,
            # show only the first char_display_limit characters
            if self.c_count:
                font_charmap = font_charmap[:self.char_display_limit]

            # font_charmap_string = '   '.join([char for char in font_charmap])
            font_charmap_string = '   '.join([char for char in font_charmap if char.isprintable()])
            self.charmaps_label.override_font(self.font_description)
            self.charmaps_label.set_text(font_charmap_string)


    def on_more_button_clicked(self, button):
        """
        This function handles the clicking of the "more" button by the user.
        It increases the character display limit by 10,000 and updates the character map of the currently selected font.
        """
        # Increase the display limit
        self.char_display_limit += 5000

        # Get the currently selected font name
        font_name, _, _ = self.get_selected_font_info()

        # Get the charmap for the selected font
        font_charmap, _, _ = self.font_charmaps[font_name]

        # Trim the charmap to the current display limit
        font_charmap = font_charmap[:self.char_display_limit]

        # Update the UI to show the character map
        font_charmap_string = '   '.join([char for char in font_charmap if char.isprintable()])
        self.charmaps_label.override_font(self.font_description)
        self.charmaps_label.set_text(font_charmap_string)


    def update_fonts_list(self):

        if not self.font_charmaps:
            print("setting font_charmaps")
            self.font_charmaps = get_fonts_charmaps()

        # Get a list of font names sorted alphabetically
        font_names = sorted(list(self.font_charmaps.keys()))

        # Populate the list store with the sorted font names
        self.fonts_list.clear()
        for font_name in font_names:
            self.fonts_list.append([font_name])


    def update_charmap_size(self, new_size):
        font_description = self.charmaps_label.get_style_context().get_font(Gtk.StateFlags.NORMAL)
        font_description.set_size(new_size * Pango.SCALE)
        self.charmaps_label.override_font(font_description)


    def on_increase_button_clicked(self, button):
        context = self.charmaps_label.get_style_context()
        current_font_desc = context.get_font(Gtk.StateFlags.NORMAL)
        current_size = current_font_desc.get_size() // Pango.SCALE
        new_size = current_size + 1
        self.update_charmap_size(new_size)


    def on_decrease_button_clicked(self, button):
        context = self.charmaps_label.get_style_context()
        current_font_desc = context.get_font(Gtk.StateFlags.NORMAL)
        current_size = current_font_desc.get_size() // Pango.SCALE
        new_size = max(1, current_size - 1)
        self.update_charmap_size(new_size)


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

            # Run font cache update and read the charmaps for the new font in parallel
            update_cache_thread = Thread(target=self.update_font_cache)
            update_cache_thread.start()

            font_charmap = self.read_charmaps(filepath)

            # Wait for the update cache thread to complete
            update_cache_thread.join()

            # Add the font and its charmaps to the dictionary
            font_filename = os.path.basename(filepath)
            font_name, _ = os.path.splitext(font_filename)
            self.font_charmaps[font_name] = (font_charmap, len(font_charmap), True)
            # Update the UI to show the new font in the list
            self.update_fonts_list()

        except Exception as e:
            print(f"An error occurred: {e}")

        dialog.destroy()


    def update_font_cache(self):
        subprocess.run(["fc-cache", "-f", "-v"], capture_output=True)
        subprocess.run(["fc-cache", "-f", "-v", "-r"], capture_output=True)


    def read_charmaps(self, filepath):

        def get_charmap(font_path):
            result = subprocess.run(['fc-query', '--format=%{charset}\n', font_path], stdout=subprocess.PIPE, text=True)
            charmap_raw = result.stdout

            charmap = []
            for range_str in re.findall(r'([0-9a-fA-F]+)-?([0-9a-fA-F]+)?', charmap_raw):
                start, end = range_str
                start = int(start, 16)
                end = int(end, 16) if end else start
                for i in range(start, min(end, 0x110000) + 1):
                    charmap.append(chr(i))

            return charmap

        font_charmap = get_charmap(filepath)
        return font_charmap


    def update_sample_text(self, widget):
        if self.font_description is not None:
            text = self.entry.get_text()
            # if text is None:
            #     text = "The quick brown fox jumps over the lazy dog."
            self.label.override_font(self.font_description)
            self.label.set_text(self.entry.get_text() if self.entry.get_text().strip() != "" else self.sample_text)


    def on_info_button_clicked(self, button):
        """
        This function is called when the info button is clicked.
        It creates a new dialog with a font size spin button.
        """

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
                self.label.set_text(self.entry.get_text() if self.entry.get_text().strip() != "" else self.sample_text)

            dialog.destroy()

        dialog.connect("response", on_response)


    def on_key_press_event(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname == "Delete":
            _, user_added = self.get_selected_font_info()
            if user_added:
                self.on_remove_button_clicked(None)


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

            # Remove the font from the self.font_charmaps dictionary
            del self.font_charmaps[font_name]
            self.delete_font(font_name)

            # Update the fonts list in the TreeView
            self.update_fonts_list()
