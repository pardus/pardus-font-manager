import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, Gdk, GLib
import subprocess
import shutil
import re
import time
import font_charmaps
import threading
from threading import Thread

import locale
from locale import gettext as _
locale.bindtextdomain('pardus-font-manager', '/usr/share/locale')
locale.textdomain('pardus-font-manager')
from ctypes import CDLL



class MainWindow:

    def __init__(self, app):
        self.application = app
        # Glade file handling and builder setup
        self.builder = Gtk.Builder()
        glade_file = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # Window setup
        self.window = self.builder.get_object("window")
        self.window.set_border_width(10)

        # Font charmap setup and sample text
        self.font_charmaps = {}
        self.font_names = []
        self.sample_text = _("The quick brown fox jumps over the lazy dog.")

        # Set default page (widget: vbox, name: page_list)
        self.target_page = "page_list"

        # This variable represents whether an operation (add, remove, search)
        # is currently ongoing in the application.
        self.operation_in_progress = False

        # Widget extraction from Glade file
        # Top-level widgets
        top_box = self.builder.get_object("top_box")
        self.vbox = self.builder.get_object("vbox")
        hbox = self.builder.get_object("hbox")
        self.main_box = self.builder.get_object("main_box")

        self.vbox_view = self.builder.get_object("vbox_view")

        # Buttons and dialog
        self.menu_button = self.builder.get_object("menu_button")
        self.menu_button_view = self.builder.get_object("menu_button_view")
        self.add_button = self.builder.get_object("add_button")
        self.try_button = self.builder.get_object("try_button")
        self.info_button = self.builder.get_object("info_button")
        self.ok_button = self.builder.get_object("ok_button")
        self.cancel_button = self.builder.get_object("cancel_button")
        self.info_dialog = self.builder.get_object("info_dialog")
        self.more_button = self.builder.get_object("more_button")
        self.more_button_view = self.builder.get_object("more_button_view")
        self.bottom_info_button = self.builder.get_object("bottom_info_button")
        self.bottom_info_button_view = self.builder.get_object("bottom_info_button_view")
        self.install_button_view = self.builder.get_object("install_button_view")

        # Label and entry widgets
        self.search_entry = self.builder.get_object("search_entry")
        self.entry = self.builder.get_object("entry")
        self.entry_view = self.builder.get_object("entry_view")
        self.charmaps_label = self.builder.get_object("charmaps_label")
        self.charmaps_label_view = self.builder.get_object("charmaps_label_view")
        self.label = self.builder.get_object("label_entry")
        self.label_entry_view = self.builder.get_object("label_entry_view")
        self.font_name_label = self.builder.get_object("font_name_label")
        self.font_name_label_view = self.builder.get_object("font_name_label_view")
        self.charmaps_label_view = self.builder.get_object("charmaps_label_view")
        self.font_size_label = self.builder.get_object("font_size_label")
        self.font_color_label = self.builder.get_object("font_color_label")
        self.bottom_info_label = self.builder.get_object("bottom_info_label")

        # Additional widgets
        self.left_scrolled = self.builder.get_object("left_scrolled")
        self.left_scrolled_box = self.builder.get_object("left_scrolled_box")
        self.right_font_box = self.builder.get_object("right_font_box")
        self.right_scrolled = self.builder.get_object("right_scrolled")
        self.stack_start = self.builder.get_object("stack_start")
        self.stack_map = self.builder.get_object("stack_map")
        self.page_charmap = self.builder.get_object("page_charmap")
        self.page_list = self.builder.get_object("page_list")
        self.spinner_start = self.builder.get_object("spinner_start")
        self.color_button = self.builder.get_object("color_button")
        self.spin_button = self.builder.get_object("spin_button")
        self.size_spin_button = self.builder.get_object("size_spin_button")
        self.size_spin_button_view = self.builder.get_object("size_spin_button_view")
        self.remove_button = self.builder.get_object("remove_button")
        self.increase_button = self.builder.get_object("increase_button")
        self.increase_button_view = self.builder.get_object("increase_button_view")
        self.decrease_button = self.builder.get_object("decrease_button")
        self.decrease_button_view = self.builder.get_object("decrease_button_view")
        self.title_box = self.builder.get_object("title_box")
        self.mlozturk = self.builder.get_object("mlozturk")
        self.fonts_view = self.builder.get_object("fonts_view")
        self.menu_popover = self.builder.get_object("menu_popover")
        self.menu_about = self.builder.get_object("menu_about")
        self.menu_settings = self.builder.get_object("menu_settings")
        self.bottom_revealer = self.builder.get_object("bottom_revealer")
        self.bottom_stack = self.builder.get_object("bottom_stack")
        self.bottom_progressbar = self.builder.get_object("bottom_progressbar")
        self.bottom_entry = self.builder.get_object("bottom_entry")
        self.bottom_scrolled = self.builder.get_object("bottom_scrolled")
        self.popover_seperator = self.builder.get_object("popover_seperator")

        self.dialog_font_manager = self.builder.get_object("dialog_font_manager")
        self.dialog_font_manager.set_program_name(_("Pardus Font Manager"))
        self.dialog_font_manager.set_transient_for(self.window)

        self.libfontadder = CDLL(os.path.join(os.getcwd(), "libfontadder.so"))

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.dialog_font_manager.set_version(version)
        except:
            pass

        # Adjustment setup for size_spin_button
        adjustment = Gtk.Adjustment.new(12, 1, 96, 1, 10, 0)
        self.size_spin_button.set_adjustment(adjustment)
        self.size_spin_button_view.set_adjustment(adjustment)

        # Start spinner
        self.spinner_start.start()

        # Signal connection for widgets
        self.search_entry.connect("changed", self.on_search_entry_changed)
        self.entry.connect("changed", self.update_sample_text)
        self.entry.connect("activate", self.update_sample_text)
        self.entry_view.connect("changed", self.update_sample_view_text)
        self.entry_view.connect("activate", self.update_sample_view_text)
        self.add_button.connect("clicked", self.on_add_button_clicked)
        self.info_button.connect("clicked", self.on_info_button_clicked)
        self.remove_button.connect("clicked", self.on_remove_button_clicked)
        self.increase_button.connect("clicked", self.on_increase_button_clicked)
        self.increase_button_view.connect("clicked", self.on_increase_button_view_clicked)
        self.decrease_button.connect("clicked", self.on_decrease_button_clicked)
        self.decrease_button_view.connect("clicked", self.on_decrease_button_view_clicked)
        self.menu_about.connect("clicked", self.on_menu_about_clicked)
        self.more_button.connect("clicked", self.on_more_button_clicked)
        self.bottom_info_button.connect("clicked", self.on_bottom_info_button_clicked)
        self.install_button_view.connect("clicked", self.install_button_view_clicked)

        # Signal connection for spin buttons
        self.size_spin_button.connect("value-changed", self.on_size_spin_button_value_changed)
        self.size_spin_button_view.connect("value-changed", self.on_size_spin_button_view_value_changed)

        # Fonts list and TreeView setup
        self.fonts_list = Gtk.ListStore(str, str) # Font name & font path
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
        self.bottom_info_button.set_visible(False)

        self.info_message = ""

        self.menu_settings.hide()
        self.popover_seperator.hide()

        # Font description initialization
        self.font_description = None
        self.char_display_limit = 2000
        self.c_count = False

        # Window properties setup
        self.window.set_title(_("Pardus Font Manager"))
        self.window.set_default_size(800, 600)
        self.window.set_application(app)
        self.controlArgs()


    def controlArgs(self):
        pass

    def check_if_font_exists(self, font_file_path):
        font_family, font_style = font_charmaps.get_font_name_from_file(font_file_path)
        font_name = f"{font_family} {font_style}"
        self.font_names = font_charmaps.get_font_names()
        for font_tuple in self.font_names:
            existing_font_name = f"{font_tuple[0]} {font_tuple[1]}"
            if font_name == existing_font_name:
                return True
        return False


    def install_button_view_clicked(self, button):

        if self.install_button_view.action:
            print("install  ....")
        else:
            print("uninstall ....")
        print(self.install_button_view.get_label())


    def worker(self):
        # self.font_charmaps = get_fonts_charmaps()
        self.update_fonts_list()
        self.set_page()
        # self.bottomrevealer.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)
        # self.bottomrevealer.set_transition_duration(200)


    def set_page(self):
        GLib.idle_add(self.stack_start.set_visible_child_name, self.target_page)
        GLib.idle_add(self.menu_button.set_sensitive, True)


    def loading_finished(self):
        self.spinner_start.stop()
        self.stack_start.set_visible_child_name("page_list")


    def on_size_spin_button_value_changed(self, spin_button):
        new_font_size = spin_button.get_value_as_int()
        self.update_sample_text_size(new_font_size)


    def on_size_spin_button_view_value_changed(self, spin_button):
        new_font_size = spin_button.get_value_as_int()
        self.update_view_sample_text_size(new_font_size)


    def on_bottom_info_button_clicked(self, button):
        self.bottom_revealer.set_reveal_child(False)


    def update_sample_text_size(self, new_size):
        if self.font_description is not None:
            self.font_description.set_size(new_size * Pango.SCALE)
            self.label.override_font(self.font_description)
            self.label.set_text(self.entry.get_text()
                                if self.entry.get_text().strip() != ""
                                else self.sample_text)


    def update_view_sample_text_size(self, new_size):
        if self.font_description is not None:
            self.font_description.set_size(new_size * Pango.SCALE)
            self.label_entry_view.override_font(self.font_description)
            self.label_entry_view.set_text(self.entry_view.get_text()
                                           if self.entry_view.get_text().strip() != ""
                                           else self.sample_text)


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
        if self.operation_in_progress:
            return

        self.operation_in_progress = True

        search_text = search_entry.get_text().lower()

        try:
            # If the search box is empty, show all fonts
            if not search_text:
                self.update_fonts_list()
                return

            # Filter the font list by matching the search string with the font names and styles
            filtered_fonts = [font_name for font_name in self.font_names
                            if search_text in font_name[0].lower() or search_text in font_name[1].lower()]
            # Clear the current list of fonts
            self.fonts_list.clear()

            # Populate the list with the filtered fonts,
            #  also sort the fonts alphabetically before adding them to the list
            for font_name, style, path in sorted(filtered_fonts):
                formatted_font_name = f"{font_name} ({style})"
                self.fonts_list.append([formatted_font_name, path])

        finally:
            self.operation_in_progress = False


    def get_selected_font_info(self):
        """
        Get the font name and user_added status of the selected font.

        Returns:
            The font name as a string and user_added status as a boolean.
        """
        selection = self.fonts_view.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            display_name, path = model[treeiter]
            name, style = display_name[:-1].split(' (')
            formatted_font_name = (name, style, path)
            # print("Font name = ", display_name)
            # print("part 1 = ", name)
            # print("part 2 =", style)
            # print("formatted name = ", formatted_font_name)

            if formatted_font_name in self.font_names:
                # Get the charmap, charmap count, and user_added flag for the
                # selected font
                self.font_charmaps = font_charmaps.get_selected_font_charmaps(name, style)

                _, charmap_count, user_added = self.font_charmaps[name, style]
            else:
                print(f"Font {name} not found in font_charmaps")
                return None, None, False, None

            if charmap_count > self.char_display_limit:
                # print(f"'{font_name}' includes {charmap_count -
                # self.char_display_limit}  more characters than what is
                # shown.")
                # self.info_message = (f"'{font_name}' includes {charmap_count - self.char_display_limit}
                # more characters, click the button for the rest of the characters.")
                self.more_button.set_visible(True)
                self.c_count = True
                # self.bottom_revealer.set_reveal_child(True)
                # self.bottom_stack.set_visible_child_name("error")
                # self.bottom_info_label.set_markup("<span color='green'>{}</span>".format(self.info_message))
            else:
                self.more_button.set_visible(False)
                self.c_count = False
                self.bottom_revealer.set_reveal_child(False)


            return name, style, user_added, self.c_count
        return None, None, False, None


    def get_remaining_elements(self, lst):
        """
        This function takes a list of strings as input and returns a new list
        containing all the elements from the input list starting from the first
        element that doesn't start with any whitespace or carriage return characters ('\r', ' '),
        and skipping any elements that start with the same character(s)
        as the first non-whitespace element.
        """
        first_element = [e for e in lst[0] if e not in ('\r', ' ', '\\u')]
        remaining_elements = []
        for i in range(1, len(lst)):
            if lst[i][0] in first_element:
                continue
            else:
                remaining_elements = lst[i:]
                break
        return remaining_elements


    def on_font_selected(self, selection):
        """
        This function handles the selection of a font by the user.
        It gets the selected font from the font selection dialog,
        sets the font description of the label to the selected font,
        displays the character map of the font, and shows a spinner
        while the character map is being displayed.
        """
        if self.operation_in_progress:
            return

        # If no selection provided, use the current one
        if not selection:
            selection = self.fonts_view.get_selection()

        font_name, style, user_added, self.c_count = self.get_selected_font_info()

        # Reset the display limit
        self.char_display_limit = 2000
        if font_name is not None:
            font_description_str = f"{font_name} {style}"
            self.font_description = Pango.FontDescription.from_string(font_description_str)

            # Show the remove button only for the fonts that have been added by the user
            self.remove_button.set_sensitive(user_added)

            self.label.override_font(self.font_description)
            self.label.set_text(self.entry.get_text() if self.entry.get_text().strip() != "" else self.sample_text)

            # Get the charmap, char_map_count and user_added flag for the selected font
            font_charmap, _, _ = self.font_charmaps[(font_name, style)]

            # Gives more info about selected font
            self.info_button.set_sensitive(True)

            # If the character count is more than char_display_limit,
            # show only the first char_display_limit characters
            if self.c_count:
                font_charmap = font_charmap[:self.char_display_limit]

            # This section was added due to the problem of listing charmaps of fonts that
            # contain spaces or similar characters in charmaps in charmaps
            font_charmap_without_gap = self.get_remaining_elements(font_charmap)
            font_charmap_string = '   '.join([char for char in font_charmap_without_gap if char != ' '])

            # # # font_charmap_string = '   '.join([char for char in font_charmap])
            # # font_charmap_string = '   '.join([char for char in font_charmap if char.isprintable()])
            # font_charmap_string = '   '.join([char for char in font_charmap if not char.isspace()])

            self.charmaps_label.override_font(self.font_description)
            self.charmaps_label.set_text(font_charmap_string)


    def on_more_button_clicked(self, button):
        """
        This function handles the clicking of the "more" button by the user.
        It increases the character display limit by 10,000 and updates the character map of the currently selected font.
        """
        self.operation_in_progress = True

        # Increase the display limit
        self.char_display_limit += 2000

        # Get the currently selected font name
        font_name, style, _, _ = self.get_selected_font_info()
        style = style.rstrip(")")
        font_key = (font_name, style)

        # Get the charmap for the selected font
        font_charmap, _, _ = self.font_charmaps[font_key]

        # Trim the charmap to the current display limit
        font_charmap = font_charmap[:self.char_display_limit]

        font_charmap_without_gap = self.get_remaining_elements(font_charmap)
        font_charmap_string = '   '.join([char for char in font_charmap_without_gap if char != ' '])

        # Update the UI to show the character map
        # font_charmap_string = '   '.join([char for char in font_charmap])
        self.charmaps_label.override_font(self.font_description)
        self.charmaps_label.set_text(font_charmap_string)
        self.operation_in_progress = False


    def update_fonts_list(self):
        self.operation_in_progress = True
        self.font_names = font_charmaps.get_font_names()

        # Get a list of font names sorted alphabetically
        self.font_names = sorted(set(self.font_names))

        # Populate the list store with the sorted font names
        self.fonts_list.clear()
        for font_name in self.font_names:
            name, style, path = font_name
            display_name = f"{name} ({style})"
            self.fonts_list.append([display_name, path])

        self.operation_in_progress = False


    def update_charmap_size(self, new_size):
        font_description = self.charmaps_label.get_style_context().get_font(Gtk.StateFlags.NORMAL)
        font_description.set_size(new_size * Pango.SCALE)
        self.charmaps_label.override_font(font_description)


    def update_charmap_size_view(self, new_size):
        font_description = self.charmaps_label_view.get_style_context().get_font(Gtk.StateFlags.NORMAL)
        font_description.set_size(new_size * Pango.SCALE)
        self.charmaps_label_view.override_font(font_description)


    def on_increase_button_clicked(self, button):
        context = self.charmaps_label.get_style_context()
        current_font_desc = context.get_font(Gtk.StateFlags.NORMAL)
        current_size = current_font_desc.get_size() // Pango.SCALE
        new_size = current_size + 1
        self.update_charmap_size(new_size)


    def on_increase_button_view_clicked(self, button):
        context = self.charmaps_label_view.get_style_context()
        current_font_desc = context.get_font(Gtk.StateFlags.NORMAL)
        current_size = current_font_desc.get_size() // Pango.SCALE
        new_size = current_size + 1
        self.update_charmap_size_view(new_size)


    def on_decrease_button_clicked(self, button):
        context = self.charmaps_label.get_style_context()
        current_font_desc = context.get_font(Gtk.StateFlags.NORMAL)
        current_size = current_font_desc.get_size() // Pango.SCALE
        new_size = max(1, current_size - 1)
        self.update_charmap_size(new_size)


    def on_decrease_button_view_clicked(self, button):
        context = self.charmaps_label_view.get_style_context()
        current_font_desc = context.get_font(Gtk.StateFlags.NORMAL)
        current_size = current_font_desc.get_size() // Pango.SCALE
        new_size = max(1, current_size - 1)
        self.update_charmap_size_view(new_size)


    def make_widgets_insensitive(self, widgets):
        for widget in widgets:
            widget.set_sensitive(False)


    def make_widgets_sensitive(self, widgets):
        for widget in widgets:
            widget.set_sensitive(True)


    def on_add_button_clicked(self, button):
        """
        This function allows the user to select a font file,
        copies the font file to the user's font directory,
        updates the font cache, and reads the charmaps for the new font.
        Then it adds the font and its charmaps to a dictionary and
        updates font list in the UI.
        """
        # Widgets to disable
        widgets = [self.add_button, self.remove_button, self.left_scrolled,
                   self.search_entry, self.entry, self.right_font_box, self.right_scrolled,
                   self.bottom_scrolled, self.bottom_entry, self.menu_button]

        self.operation_in_progress = True
        dialog = Gtk.FileChooserDialog(_(
            "Please choose a font file"), self.window, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        filter_ttf = Gtk.FileFilter()
        filter_ttf.set_name(_("TTF files"))
        filter_ttf.add_mime_type("application/x-font-ttf")
        dialog.add_filter(filter_ttf)

        filter_otf = Gtk.FileFilter()
        filter_otf.set_name(_("OTF files"))
        filter_otf.add_mime_type("application/x-font-otf")
        dialog.add_filter(filter_otf)

        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            dialog.destroy()
            self.operation_in_progress = False
            widgets.remove(self.remove_button)
            GLib.idle_add(self.make_widgets_sensitive, widgets)
            return

        self.make_widgets_insensitive(widgets)

        filepath = dialog.get_filename()
        result = self.libfontadder.fontmain(filepath.encode('utf-8'))

        dialog.destroy()

        def load_font():
            try:
                font_family, font_style = font_charmaps.get_font_name_from_file(filepath)

                # Combine family and style for a unique font name
                fname = f"{font_family} {font_style}"

                if not font_family or not font_style:
                    self.show_error("Unable to extract font name from the selected file.")
                    return

                # Check if the font is already installed
                font_already_exists = False
                for font_tuple in self.font_names:
                    existing_font_name = f"{font_tuple[0]} {font_tuple[1]}"
                    if fname == existing_font_name:
                        font_already_exists = True
                        break

                if font_already_exists:
                    self.info_message = "{} {} {}".format(_("The font"), fname, _("is already installed!"))
                    widgets.remove(self.remove_button)
                    GLib.idle_add(self.show_error, self.info_message)
                    return

                # Start pulsing the progress bar
                GLib.idle_add(self.start_progress_bar, 0)  # Pass progress stage

                # Create the .fonts directory if it doesn't exist
                os.makedirs(os.path.expanduser("~/.fonts"), exist_ok=True)
                time.sleep(0.5)
                GLib.idle_add(self.start_progress_bar, 40)  # Update progress stage

                # Copy the font file to ~/.fonts
                shutil.copy2(filepath, os.path.expanduser("~/.fonts"))
                time.sleep(0.5)
                GLib.idle_add(self.start_progress_bar, 70)  # Update progress stage

                # Get charmaps of the new font
                new_font_charmaps = font_charmaps.get_font_charmaps(filepath)

                # Update self.font_charmaps
                for font_name, (char_list, charmap_count) in new_font_charmaps.items():
                    user_added = filepath.startswith(os.path.expanduser("~"))
                    self.font_charmaps[font_name] = (char_list, charmap_count, user_added)

                # Run font cache update and read the charmaps for the new font in parallel
                update_cache_thread = Thread(target=self.update_font_cache)
                update_cache_thread.start()
                time.sleep(0.5)
                GLib.idle_add(self.start_progress_bar, 90)  # Update progress stage

                font_charmap = self.read_charmaps(filepath)
                time.sleep(0.5)
                GLib.idle_add(self.start_progress_bar, 100)  # Update progress stage

                # Add the font and its charmaps to the dictionary
                self.font_charmaps[font_name] = (font_charmap, len(font_charmap), True)

            except Exception as e:
                GLib.idle_add(self.show_error, f"An error occurred: {e}")
            else:
                GLib.idle_add(self.finish_adding_font, fname)
            finally:
                self.operation_in_progress = False
                GLib.idle_add(self.make_widgets_sensitive, widgets)

        threading.Thread(target=load_font).start()


    def start_progress_bar(self, progress):
        self.bottom_revealer.set_reveal_child(True)
        self.bottom_stack.set_visible_child_name("progress")
        self.bottom_progressbar.set_fraction(progress / 100.0)


    def show_error(self, message):
        self.bottom_revealer.set_reveal_child(True)
        self.bottom_stack.set_visible_child_name("error")
        self.bottom_info_label.set_markup("<span color='red'>{}</span>".format(message))


    def finish_adding_font(self, fname, error=None):
        self.update_fonts_list()
        if error is None:
            self.bottom_stack.set_visible_child_name("error")
            self.info_message = "{} {} {}".format(_("The font"), fname, _("has been added successfully"))

            self.bottom_info_label.set_markup("<span color='green'>{}</span>".format(self.info_message))
        else:
            self.bottom_stack.set_visible_child_name("error")
            self.info_message = "{} {} : {}".format(_("An error occurred while adding the font"), fname, error)
            self.bottom_info_label.set_markup("<span color='red'>{}</span>".format(self.info_message))
        self.bottom_revealer.set_reveal_child(True)

        # After adding the font, apply the search filter.
        self.on_search_entry_changed(self.search_entry)


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
            self.label.set_text(self.entry.get_text()
                                if self.entry.get_text().strip() != ""
                                else self.sample_text)


    def update_sample_view_text(self, widget):
        if self.font_description is not None:
            self.label_entry_view.override_font(self.font_description)
            self.label_entry_view.set_text(self.entry_view.get_text()
                                           if self.entry_view.get_text().strip() != ""
                                           else self.sample_text)


    def on_info_button_clicked(self, button):
        """
        This function is called when the info button is clicked.
        It creates a new dialog with a font size spin button.
        """

        dialog = Gtk.Dialog(title="Font Info", parent=self.window, flags=0)
        dialog.set_default_size(300, 300)
        dialog.set_modal(True)

        # Create the spin button for font size
        font_size_label = Gtk.Label(_("Font Size:"))
        font_size_spin_button = Gtk.SpinButton.new_with_range(8, 96, 2)
        font_size_spin_button.set_value(int(self.font_description.get_size() / Pango.SCALE))

        # Add the font size spin button to the dialog
        dialog_box = dialog.get_content_area()
        dialog_box.add(font_size_label)
        dialog_box.add(font_size_spin_button)

        # Add an "OK" button to the dialog box
        ok_button = dialog.add_button(_("OK"), Gtk.ResponseType.OK)

        # Add a "Cancel" button to the dialog box
        cancel_button = dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)

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


    def confirm_delete(self):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("Delete Font?"),
        )
        dialog.format_secondary_text(
            _("Are you sure you want to delete this font? This action cannot be undone.")
        )
        response = dialog.run()
        dialog.destroy()  # Destroy the dialog regardless of the response

        if response == Gtk.ResponseType.YES:
            # Proceed with deletion
            return True

        return False


    def select_font_at_path(self, path):
        """
        Ensures that the selection stays at the index following the font
        selected for deletion.

        Args:
        path (Gtk.TreePath): The path of the font in TreeView.
        """
        self.fonts_view.get_selection().select_path(path)
        self.fonts_view.scroll_to_cell(path, None, True, 0.5, 0.5)


    def show_info(self, message):
        self.bottom_revealer.set_reveal_child(True)
        self.bottom_stack.set_visible_child_name("error")
        self.bottom_info_label.set_markup("<span color='green'>{}</span>".format(message))
        # Hide the message after 4 seconds
        GLib.timeout_add_seconds(4, lambda: self.bottom_revealer.set_reveal_child(False))


    def delete_font(self, font_path):
        """Delete the font given its file path."""

        font_file = font_path
        print(f"font_file: {font_file}")
        if font_file:
            font_folder = os.path.dirname(font_file)

            # Start the progress bar at 0
            GLib.idle_add(self.start_progress_bar, 0)

            os.remove(font_file)

            time.sleep(0.5)
            GLib.idle_add(self.start_progress_bar, 50)

            font_name = os.path.basename(font_file)
            self.info_message = "{}: {}".format(_("Deleted font file:"), font_file)

            # Delete the parent directory if it is empty
            if not os.listdir(font_folder):
                os.rmdir(font_folder)
                print(f"Deleted empty folder: {font_folder}")

                # Update the progress bar to 80 after deleting the folder
                time.sleep(0.5)
                GLib.idle_add(self.start_progress_bar, 80)

        # Update the progress bar to 100 when everything is done
        time.sleep(0.5)
        GLib.idle_add(self.start_progress_bar, 100)
        time.sleep(0.1)
        GLib.timeout_add_seconds(1, self.show_info,
                                "{} {} {}".format(_("The font"), font_name, _("has been deleted successfully")))


    def delete_selected_font(self):
        if self.operation_in_progress:
            return

        self.operation_in_progress = True
        selection = self.fonts_view.get_selection()
        model, iter_ = selection.get_selected()

        if not iter_:
            self.operation_in_progress = False
            return

        font_path = model[iter_][1]
        display_name = model[iter_][0]
        name, style = display_name[:-1].split(' (')

        if not self.confirm_delete():
            self.operation_in_progress = False
            return

        def delete_font_and_update():
            try:
                del self.font_charmaps[(name, style)]
                self.delete_font(font_path)
                self.update_font_cache()

                GLib.idle_add(self.update_fonts_list)
                GLib.idle_add(self.select_font_at_path, model.get_path(iter_))
            finally:
                self.operation_in_progress = False
                # After deleting the font, apply the search filter.
                GLib.idle_add(self.on_search_entry_changed, self.search_entry)


        threading.Thread(target=delete_font_and_update).start()


    def on_key_press_event(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname == "Delete":
            _, user_added, _, _ = self.get_selected_font_info()
            if user_added:
                self.delete_selected_font()


    def on_remove_button_clicked(self, button):
        # Widgets to disable
        widgets = [self.add_button, self.remove_button, self.left_scrolled,
                   self.search_entry, self.entry, self.right_font_box,
                   self.right_scrolled, self.bottom_scrolled, self.bottom_entry,
                   self.menu_button]

        self.make_widgets_insensitive(widgets)
        self.delete_selected_font()
        self.make_widgets_sensitive(widgets)
