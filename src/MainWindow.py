import os
import subprocess
import threading
from threading import Thread
import locale
from ctypes import CDLL

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, Gdk, GLib

import font_charmaps
import add_font
import delete_font

locale.bindtextdomain('pardus-font-manager', '/usr/share/locale')
locale.textdomain('pardus-font-manager')
_ = locale.gettext


class MainWindow:

    def __init__(self, app):
        self.application = app

        # Glade file handling and builder setup
        self.builder = Gtk.Builder()
        glade_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "../ui/MainWindow.glade")
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # Window setup
        self.window = self.builder.get_object("window")
        self.window.set_border_width(10)
        self.target_page = "page_list"  # Set default page

        # Font charmap setup and sample text
        self.font_charmaps = {}
        self.font_names = []
        self.info_message = ""
        self.sample_text = _("The quick brown fox jumps over the lazy dog.")

        # This variable represents whether an operation (add, remove, search)
        # is currently ongoing in the application.
        self.operation_in_progress = False

        # Dynamic library for font addition
        self.libfontadder = CDLL(
            "/usr/share/pardus/pardus-font-manager/src/libfontadder.so"
        )
        # self.libfontadder = CDLL(os.path.join(os.getcwd(), "libfontadder.so"))

        self.defineComponents()

        # Set version if it cannot be retrieved from __version__ file,
        # then use MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) +
                           "/__version__").readline()
            self.dialog_font_manager.set_version(version)
        except:
            pass

        # Threading setup for background tasks
        p1 = Thread(target=self.worker, daemon=True)
        p1.start()

        # Font display settings
        self.c_count = False
        self.char_display_limit = 2000
        self.font_description = None
        self.multiple_select_active = False
        self.fonts_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

        # Currently hiding settings in UI
        self.menu_settings.hide()
        self.popover_seperator.hide()

        # Window display
        self.window.show_all()
        self.window.set_title(_("Pardus Font Manager"))
        self.window.set_default_size(800, 600)
        self.window.set_application(app)
        self.control_args()


    def defineComponents(self):
        # Widget extraction from Glade file
        # Boxes
        self.bottom_entry_box = self.builder.get_object("bottom_entry_box")
        self.right_font_box = self.builder.get_object("right_font_box")

        # Buttons
        self.menu_button = self.builder.get_object("menu_button")
        self.menu_button_view = self.builder.get_object("menu_button_view")
        self.add_button = self.builder.get_object("add_button")
        self.try_button = self.builder.get_object("try_button")
        self.ok_button = self.builder.get_object("ok_button")
        self.cancel_button = self.builder.get_object("cancel_button")
        self.menu_about = self.builder.get_object("menu_about")
        self.menu_settings = self.builder.get_object("menu_settings")
        self.more_button = self.builder.get_object("more_button")
        self.more_button_view = self.builder.get_object("more_button_view")
        self.bottom_info_button = self.builder.get_object("bottom_info_button")
        self.bottom_info_button_view = self.builder.get_object(
            "bottom_info_button_view"
        )
        self.install_button_view = self.builder.get_object("install_button_view")
        self.color_button = self.builder.get_object("color_button")
        self.spin_button = self.builder.get_object("spin_button")
        self.size_spin_button = self.builder.get_object("size_spin_button")
        self.size_spin_button_view = self.builder.get_object("size_spin_button_view")
        self.remove_button = self.builder.get_object("remove_button")
        self.increase_button = self.builder.get_object("increase_button")
        self.increase_button_view = self.builder.get_object("increase_button_view")
        self.decrease_button = self.builder.get_object("decrease_button")
        self.decrease_button_view = self.builder.get_object("decrease_button_view")
        # self.info_button = self.builder.get_object("info_button")

        # Entries
        self.search_entry = self.builder.get_object("search_entry")
        self.entry = self.builder.get_object("entry")
        self.entry_view = self.builder.get_object("entry_view")
        self.label = self.builder.get_object("label_entry")
        self.label_entry_view = self.builder.get_object("label_entry_view")

        # Labels
        self.charmaps_label = self.builder.get_object("charmaps_label")
        self.charmaps_label_view = self.builder.get_object("charmaps_label_view")
        self.font_name_label = self.builder.get_object("font_name_label")
        self.font_name_label_view = self.builder.get_object("font_name_label_view")
        self.charmaps_label_view = self.builder.get_object("charmaps_label_view")
        self.font_size_label = self.builder.get_object("font_size_label")
        self.font_color_label = self.builder.get_object("font_color_label")
        self.bottom_info_label = self.builder.get_object("bottom_info_label")
        self.waterfall_label = self.builder.get_object("waterfall_label")
        self.lipsum_label = self.builder.get_object("lipsum_label")

        # Additional widgets
        self.left_scrolled = self.builder.get_object("left_scrolled")
        self.right_scrolled = self.builder.get_object("right_scrolled")
        self.stack_start = self.builder.get_object("stack_start")
        self.stack_map = self.builder.get_object("stack_map")
        self.page_charmap = self.builder.get_object("page_charmap")
        self.page_list = self.builder.get_object("page_list")
        self.mlozturk = self.builder.get_object("mlozturk")
        self.fonts_view = self.builder.get_object("fonts_view")
        self.menu_popover = self.builder.get_object("menu_popover")
        self.bottom_revealer = self.builder.get_object("bottom_revealer")
        self.bottom_stack = self.builder.get_object("bottom_stack")
        self.bottom_progressbar = self.builder.get_object("bottom_progressbar")
        self.bottom_scrolled = self.builder.get_object("bottom_scrolled")
        self.revealer_scrolled = self.builder.get_object("revealer_scrolled")
        self.popover_seperator = self.builder.get_object("popover_seperator")

        # Comboboxes
        self.charmaps_combo = self.builder.get_object("charmaps_combo")
        self.charmaps_combo.append_text(_("Characters"))
        self.charmaps_combo.append_text(_("Waterfall"))
        self.charmaps_combo.append_text("Lorem Ipsum")
        self.charmaps_combo.set_active(0)

        # Dialogs
        self.dialog_settings = self.builder.get_object("dialog_settings")
        self.dialog_font_manager = self.builder.get_object("dialog_font_manager")
        self.dialog_font_manager.set_program_name(_("Pardus Font Manager"))
        self.dialog_font_manager.set_transient_for(self.window)
        if self.dialog_font_manager.get_titlebar() is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("About Pardus Font Manager"))
            about_headerbar.pack_start(
                Gtk.Image.new_from_icon_name(
                    "pardus-font-manager", Gtk.IconSize.LARGE_TOOLBAR
                )
            )
            about_headerbar.show_all()
            self.dialog_font_manager.set_titlebar(about_headerbar)

        # Button sensitivity and visibility setup
        self.bottom_info_button.set_visible(False)
        self.menu_button.set_sensitive(False)
        self.more_button.set_visible(False)
        self.remove_button.set_sensitive(False)
        # self.info_button.set_sensitive(False)
        # self.info_button.set_visible(False)

        # Adjustment setup for size_spin_button
        adjustment = Gtk.Adjustment.new(12, 1, 96, 1, 10, 0)
        self.size_spin_button.set_adjustment(adjustment)
        self.size_spin_button_view.set_adjustment(adjustment)

        # Font list and TreeView setup
        self.fonts_list = Gtk.ListStore(str, str)  # Font name & font path
        self.fonts_view.set_headers_visible(False)
        self.fonts_view.set_model(self.fonts_list)
        self.fonts_view.append_column(
            Gtk.TreeViewColumn("Fonts", Gtk.CellRendererText(), text=0)
        )

        # Signal connection for widgets
        self.search_entry.connect("changed", self.on_search_entry_changed)
        self.entry.connect("changed", self.update_sample_text)
        self.entry.connect("activate", self.update_sample_text)
        self.entry_view.connect("changed", self.update_sample_view_text)
        self.entry_view.connect("activate", self.update_sample_view_text)
        self.menu_about.connect("clicked", self.on_menu_about_clicked)
        self.more_button.connect("clicked", self.on_more_button_clicked)
        self.bottom_info_button.connect("clicked", self.on_bottom_info_button_clicked)
        self.install_button_view.connect("clicked", self.install_button_view_clicked)
        self.charmaps_combo.connect("changed", self.charmaps_combo_changed)
        self.fonts_view.get_selection().connect("changed", self.on_font_selected)
        self.fonts_view.connect("row-activated", self.on_row_activated)
        self.fonts_view.connect(
            "key-press-event",
            lambda widget, event: delete_font.on_key_press_event(widget, event, self)
        )
        self.add_button.connect(
            "clicked", lambda button: add_font.on_add_button_clicked(self, button)
        )
        self.remove_button.connect(
            "clicked",
            lambda button: delete_font.on_remove_button_clicked(self, button)
        )
        self.increase_button.connect("clicked", self.on_increase_button_clicked)
        self.increase_button_view.connect(
            "clicked", self.on_increase_button_view_clicked
        )
        self.decrease_button.connect("clicked", self.on_decrease_button_clicked)
        self.decrease_button_view.connect(
            "clicked", self.on_decrease_button_view_clicked
        )
        self.size_spin_button.connect(
            "value-changed", self.on_size_spin_button_value_changed
        )
        self.size_spin_button_view.connect(
            "value-changed", self.on_size_spin_button_view_value_changed
        )
        # self.info_button.connect("clicked", self.on_info_button_clicked)

    def worker(self):
        self.font_names = font_charmaps.get_font_names()

        GLib.idle_add(self.update_fonts_list)
        GLib.idle_add(self.set_page)

    def control_args(self):
        """
        Checks for '--details' argument followed by a font file path
        """
        if self.application.args and 'details' in self.application.args:
            font_path = self.application.args['details']
            if font_path:
                self.run_font_viewer(font_path)
            else:
                print("Font path not provided.")


    def run_font_viewer(self, font_path):
        """
        Opens font viewer window to preview the given font file
        """
        font_viewer = FontViewer(font_path)
        font_viewer.show_all()
        Gtk.main()


    def check_if_font_exists(self, font_file_path):
        font_family, font_style = font_charmaps.get_font_name_from_file(font_file_path)
        font_name = f"{font_family} {font_style}"

        # Retrieve existing font names
        self.font_names = font_charmaps.get_font_names()

        # Check if font name matches any existing font
        for font_tuple in self.font_names:
            existing_font_name = f"{font_tuple[0]} {font_tuple[1]}"
            if font_name == existing_font_name:
                return True

        return False


    def install_button_view_clicked(self, button):
        # Find a better common button name for the func
        if self.install_button_view.action:
            print("install  ....")
            add_font.on_add_button_clicked(self.install_button_view)
        else:
            print("uninstall ....")
        print(self.install_button_view.get_label())


    def set_page(self):
        GLib.idle_add(self.stack_start.set_visible_child_name, self.target_page)
        GLib.idle_add(self.menu_button.set_sensitive, True)


    def charmaps_combo_changed(self, widget):
        self.update_font_view()


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
            self.label.set_text(
                self.entry.get_text()
                if self.entry.get_text().strip() != ""
                else self.sample_text
            )


    def update_view_sample_text_size(self, new_size):
        if self.font_description is not None:
            self.font_description.set_size(new_size * Pango.SCALE)
            self.label_entry_view.override_font(self.font_description)
            self.label_entry_view.set_text(
                self.entry_view.get_text()
                if self.entry_view.get_text().strip() != ""
                else self.sample_text
            )


    def on_menu_about_clicked(self, button):
        self.menu_popover.popdown()
        self.dialog_font_manager.run()
        self.dialog_font_manager.hide()


    def on_search_entry_changed(self, search_entry):
        """
        Filters font list based on the search text, clears the current
        list of fonts, and populates font list with the filtered fonts.
        """
        if self.operation_in_progress:
            return

        self.operation_in_progress = True

        search_text = search_entry.get_text().lower()

        try:
            # If search box is empty, show all fonts
            if not search_text:
                self.update_fonts_list()
                return

            # Filter font list by matching search string with font names & styles
            filtered_fonts = [
                font_name
                for font_name in self.font_names
                if search_text in font_name[0].lower()
                or search_text in font_name[1].lower()
            ]

            # Clear current list of fonts
            self.fonts_list.clear()

            added_fonts = set()

            # Populate the list with filtered fonts, also sort fonts
            # alphabetically before adding them to the list
            for font_name, style, path in sorted(filtered_fonts):
                formatted_font_name = f"{font_name} ({style})"

                # Check if this font name has already been added
                if formatted_font_name not in added_fonts:
                    self.fonts_list.append([formatted_font_name, path])
                    added_fonts.add(formatted_font_name)

        finally:
            self.operation_in_progress = False


    def get_selected_font_info(self):
        """
        Returns font name, style, user_added status(bool), and character count
        flag of the selected fonts(bool)
        """
        selection = self.fonts_view.get_selection()
        model = self.fonts_view.get_model()

        if selection.get_mode() == Gtk.SelectionMode.MULTIPLE:
            paths = selection.get_selected_rows()[1]
            if paths:
                # Last selected font info
                treeiter = model.get_iter(paths[-1])
                display_name, path = model[treeiter]
                name, style = display_name[:-1].split(' (')
                formatted_font_name = (name, style, path)

                if formatted_font_name in self.font_names:
                    # Get charmap, charmap count, and user_added flag
                    self.font_charmaps = font_charmaps.get_selected_font_charmaps(
                        name, style
                    )
                    _, charmap_count, user_added = self.font_charmaps[name, style]
                else:
                    return None, None, False, None

                if charmap_count > self.char_display_limit:
                    self.more_button.set_visible(True)
                    self.c_count = True
                else:
                    self.more_button.set_visible(False)
                    self.c_count = False
                    self.bottom_revealer.set_reveal_child(False)

                return name, style, user_added, self.c_count
            return None, None, False, None
        else:
            treeiter = selection.get_selected()[1]
            if treeiter:
                return self.get_font_info_from_iter(model, treeiter)
            return None, None, False, None


    def get_font_info_from_iter(self, model, tree_iter):
        """
        Returns font name, style, user_added status(bool), and character
        count flag of the selected font(bool)
        """
        display_name, path = model[tree_iter]
        name, style = display_name[:-1].split(' (')
        formatted_font_name = (name, style, path)

        if formatted_font_name in self.font_names:
            self.font_charmaps = font_charmaps.get_selected_font_charmaps(name, style)
            _, charmap_count, user_added = self.font_charmaps[name, style]
        else:
            print(f"Font {name} not found in font_charmaps")
            return None, None, False, None

        if charmap_count > self.char_display_limit:
            self.more_button.set_visible(True)
            self.c_count = True
        else:
            self.more_button.set_visible(False)
            self.c_count = False
            self.bottom_revealer.set_reveal_child(False)

        return name, style, user_added, self.c_count


    def get_remaining_elements(self, lst):
        """
        Takes a list of strings and returns a new list with elements that don't
        start with spaces or carriage returns.
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
        if self.operation_in_progress:
            return

        # If no selection provided, use the current one
        if not selection:
            selection = self.fonts_view.get_selection()

        self.update_font_view()


    def update_font_view(self):
        """
        Updates UI based on the current font selection and selected element in
        charmaps combobox.
        """
        selected_element = self.charmaps_combo.get_active_text()

        font_name, style, user_added, self.c_count = self.get_selected_font_info()

        # If font was added by user, user can delete the font
        self.remove_button.set_sensitive(user_added)

        if font_name is not None:
            font_description_str = f"{font_name} {style}"
            self.font_description = Pango.FontDescription.from_string(
                font_description_str
            )

            self.label.override_font(self.font_description)
            display_text = (
                self.entry.get_text().strip()
                if self.entry.get_text().strip() != ""
                else self.sample_text
            )
            self.label.set_text(display_text)

            if selected_element == _("Waterfall"):
                self.prepare_waterfall_view(font_name, style, display_text)
                button_visibility = False
            elif selected_element == ("Lorem Ipsum"):
                self.prepare_lorem_ipsum_view(font_name, style)
                button_visibility = True
            else:
                self.prepare_charmap_view(font_name, style)
                button_visibility = True

            self.increase_button.set_visible(button_visibility)
            self.decrease_button.set_visible(button_visibility)


    def prepare_charmap_view(self, font_name, style):
        self.charmaps_label.set_line_wrap(True)
        self.char_display_limit = 2000  # Reset the display limit
        font_charmap, _, _ = self.font_charmaps[(font_name, style)]

        if self.c_count:
            font_charmap = font_charmap[: self.char_display_limit]

        font_charmap_without_gap = self.get_remaining_elements(font_charmap)
        font_charmap_string = '   '.join(
            [char for char in font_charmap_without_gap if char != ' ']
        )

        self.charmaps_label.override_font(self.font_description)
        self.charmaps_label.set_text(font_charmap_string)


    def prepare_lorem_ipsum_view(self, font_name, style):
        """
        Prepares and displays the Lorem Ipsum text in the selected font and style.
        """
        self.more_button.set_visible(False)
        self.charmaps_label.set_line_wrap(True)
        self.charmaps_label.set_xalign(0.0)

        lorem_ipsum_text = (
            "   Lorem ipsum dolor sit amet, consectetuer adipiscing elit. "
            "Aenean commodo ligula eget dolor. Aenean massa. Cum sociis "
            "natoque penatibus et magnis dis parturient montes, nascetur "
            "ridiculus mus. Donec quam felis, ultricies nec, pellentesque "
            "eu, pretium quis, sem.\n\n"
            "   Nulla consequat massa quis enim. Donec pede justo, fringilla vel, "
            "aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, "
            "imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede "
            "mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum "
            "semper nisi.\n\n"
            "   Aenean vulputate eleifend tellus. Aenean leo ligula, porttitor eu, "
            "consequat vitae, eleifend ac, enim. Aliquam lorem ante, dapibus in, "
            "viverra quis, feugiat a, tellus. Phasellus viverra nulla ut metus "
            "varius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies "
            "nisi vel augue. Curabitur ullamcorper ultricies nisi."
        )

        formatted_lorem_ipsum = f'<span font="{font_name} {style}">{lorem_ipsum_text}</span>'
        self.charmaps_label.set_markup(formatted_lorem_ipsum)


    def prepare_waterfall_view(self, font_name, style, display_text):
        self.charmaps_label.set_line_wrap(False)
        self.charmaps_label.set_xalign(0.0)

        # From 8 to 48 points
        # To see waterfall correctly, add 3x spaces if size in [8, 9]
        waterfall_text = '\n'.join(
            f'<span font="Sans 8">{"  " if size in [8, 9] else ""}{size} pt.   </span>'
            f'<span font="{font_name} {style} {size}">{display_text}</span>'
            for size in range(8, 49)
        )

        self.charmaps_label.set_markup(waterfall_text)


    def on_more_button_clicked(self, button):
        """
        Show the remaining characters if font has more than 2000 characters
        """
        self.operation_in_progress = True

        # Increase the display limit
        self.char_display_limit += 2000

        # Get the currently selected font name
        font_name, style, _, _ = self.get_selected_font_info()
        style = style.rstrip(")")
        font_key = (font_name, style)

        # Get charmap for selected font
        font_charmap, _, _ = self.font_charmaps[font_key]

        # Trim charmap to current display limit
        font_charmap = font_charmap[: self.char_display_limit]

        font_charmap_without_gap = self.get_remaining_elements(font_charmap)
        font_charmap_string = '   '.join(
            [char for char in font_charmap_without_gap if char != ' ']
        )

        # Update the UI to show the character map
        # font_charmap_string = '   '.join([char for char in font_charmap])
        self.charmaps_label.override_font(self.font_description)
        self.charmaps_label.set_text(font_charmap_string)
        self.operation_in_progress = False


    def update_fonts_list(self):
        self.operation_in_progress = True
        self.font_names = font_charmaps.get_font_names()

        # Get a list of unique font names sorted alphabetically
        seen = set()
        unique_font_names = []
        for font_name in self.font_names:
            name, style, path = font_name
            if (name, style) not in seen:
                seen.add((name, style))
                unique_font_names.append(font_name)

        # Sort the unique font names
        unique_font_names.sort(key=lambda x: x[0])

        # Populate font list store with sorted font names
        self.fonts_list.clear()
        for font_name in unique_font_names:
            name, style, path = font_name
            display_name = f"{name} ({style})"
            self.fonts_list.append([display_name, path])

        self.operation_in_progress = False


    def update_charmap_size(self, new_size):
        font_description = self.charmaps_label.get_style_context().get_font(
            Gtk.StateFlags.NORMAL
        )
        font_description.set_size(new_size * Pango.SCALE)
        self.charmaps_label.override_font(font_description)


    def update_charmap_size_view(self, new_size):
        font_description = self.charmaps_label_view.get_style_context().get_font(
            Gtk.StateFlags.NORMAL
        )
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


    def start_progress_bar(self, progress):
        self.bottom_revealer.set_reveal_child(True)
        self.bottom_stack.set_visible_child_name("progress")
        self.bottom_progressbar.set_fraction(progress / 100.0)


    def show_error(self, message):
        self.bottom_revealer.set_reveal_child(True)
        self.bottom_stack.set_visible_child_name("error")
        self.bottom_info_label.set_markup("<span color='red'>{}</span>".format(message))


    def update_font_cache(self):
        subprocess.run(["fc-cache", "-f", "-v"], capture_output=True)


    def update_sample_text(self, widget):
        if self.font_description is not None:
            text = self.entry.get_text()
            # if text is None:
            #     text = "The quick brown fox jumps over the lazy dog."
            self.label.override_font(self.font_description)
            self.label.set_text(
                self.entry.get_text()
                if self.entry.get_text().strip() != ""
                else self.sample_text
            )


    def update_sample_view_text(self, widget):
        if self.font_description is not None:
            self.label_entry_view.override_font(self.font_description)
            self.label_entry_view.set_text(
                self.entry_view.get_text()
                if self.entry_view.get_text().strip() != ""
                else self.sample_text
            )


    def on_info_button_clicked(self, button):
        dialog = Gtk.Dialog(title="Font Info", parent=self.window, flags=0)
        dialog.set_default_size(300, 300)
        dialog.set_modal(True)

        # Create the spin button for font size
        font_size_label = Gtk.Label(_("Font Size:"))
        font_size_spin_button = Gtk.SpinButton.new_with_range(8, 96, 2)
        font_size_spin_button.set_value(
            int(self.font_description.get_size() / Pango.SCALE)
        )

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
                self.label.set_text(
                    self.entry.get_text()
                    if self.entry.get_text().strip() != ""
                    else self.sample_text
                )

            dialog.destroy()

        dialog.connect("response", on_response)


    def select_font_at_path(self, path):
        """
        Ensures that the selection stays at the index following the font
        selected for deletion.
        """
        self.fonts_view.get_selection().select_path(path)
        self.fonts_view.scroll_to_cell(path, None, True, 0.5, 0.5)


    def show_info(self, message):
        self.bottom_revealer.set_reveal_child(True)
        self.bottom_stack.set_visible_child_name("error")
        self.bottom_info_label.set_markup(
            "<span color='green'>{}</span>".format(message)
        )

        GLib.timeout_add_seconds(
            4, lambda: self.bottom_revealer.set_reveal_child(False)
        )


    def on_row_activated(self, treeview, path, column):
        self.multiple_select_active = False
        self.fonts_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
