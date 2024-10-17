import os
import subprocess
import shutil
import re
import threading
from threading import Thread
import locale

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, Gdk, GLib

import font_charmaps

locale.bindtextdomain('pardus-font-manager', '/usr/share/locale')
locale.textdomain('pardus-font-manager')
_ = locale.gettext


def on_add_button_clicked(self, button):
    """
    Copies font file to user's font directory, updates font cache, and reads
    charmaps for the new font, updates UI to include new font and its charmaps
    """
    # Widgets to disable
    widgets = [
        self.add_button,
        self.bottom_scrolled,
        self.bottom_entry_box,
        self.entry,
        self.left_scrolled,
        self.menu_button,
        self.remove_button,
        self.right_font_box,
        self.right_scrolled,
        self.search_entry
    ]

    self.operation_in_progress = True

    self.added_fonts_from_dialog = []

    dialog = Gtk.FileChooserDialog(
        _("Please choose a font file"),
        self.window,
        Gtk.FileChooserAction.OPEN,
        (
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        ),
    )

    dialog.set_select_multiple(True)

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
        if self.remove_button in widgets:
            widgets.remove(self.remove_button)
        GLib.idle_add(self.make_widgets_sensitive, widgets)
        return

    self.make_widgets_insensitive(widgets)

    filepaths = dialog.get_filenames()
    dialog.destroy()

    for filepath in filepaths:
        self.libfontadder.fontmain(filepath.encode('utf-8'))

        def load_font(filepath):
            try:
                font_family, font_style = font_charmaps.get_font_name_from_file(
                    filepath
                )

                # Combine family and style for a unique font name
                fname = f"{font_family} {font_style}"

                if not font_family or not font_style:
                    self.show_error(
                        "Unable to extract font name from the selected file."
                    )
                    return

                # Check if the font is already installed
                font_already_exists = False
                for font_tuple in self.font_names:
                    existing_font_name = f"{font_tuple[0]} {font_tuple[1]}"
                    if fname == existing_font_name:
                        font_already_exists = True
                        break

                if font_already_exists:
                    self.info_message = "{} {} {}".format(
                        _("The font"), fname, _("is already installed!")
                    )
                    if self.remove_button in widgets:
                        widgets.remove(self.remove_button)
                    GLib.idle_add(self.show_error, self.info_message)
                    return

                # Start pulsing the progress bar
                GLib.idle_add(self.start_progress_bar, 0)

                # Create the .fonts directory if it doesn't exist
                os.makedirs(os.path.expanduser("~/.fonts"), exist_ok=True)
                GLib.idle_add(self.start_progress_bar, 40)

                # Copy the font file to ~/.fonts
                shutil.copy2(filepath, os.path.expanduser("~/.fonts"))
                GLib.idle_add(self.start_progress_bar, 70)

                # Get charmaps of the new font
                new_font_charmaps = font_charmaps.get_font_charmaps(filepath)

                # Update self.font_charmaps
                for font_name, (
                    char_list,
                    charmap_count,
                ) in new_font_charmaps.items():
                    user_added = filepath.startswith(os.path.expanduser("~"))
                    self.font_charmaps[font_name] = (
                        char_list,
                        charmap_count,
                        user_added,
                    )

                # Run font cache & read the charmaps for new font in parallel
                # update_cache_thread = Thread(target=self.update_font_cache)
                # update_cache_thread.start()
                self.update_font_cache()
                GLib.idle_add(self.start_progress_bar, 90)

                font_charmap = read_charmaps(filepath)
                GLib.idle_add(self.start_progress_bar, 100)

                self.added_fonts_from_dialog.append(fname)

                # Add the font and its charmaps to the dictionary
                self.font_charmaps[font_name] = (
                    font_charmap,
                    len(font_charmap),
                    True,
                )

            except Exception as e:
                GLib.idle_add(self.show_error, f"An error occurred: {e}")
            else:
                GLib.idle_add(finish_adding_font, self, error=None)
            finally:
                self.operation_in_progress = False
                GLib.idle_add(self.make_widgets_sensitive, widgets)

        threading.Thread(target=load_font, args=(filepath,)).start()


def finish_adding_font(self, error=None):
    self.update_fonts_list()

    font_names_str = ", ".join(self.added_fonts_from_dialog)

    if error is None:
        self.bottom_stack.set_visible_child_name("error")
        self.info_message = "{} {} {}".format(
            _("Fonts have been added successfully:"), font_names_str, ""
        )

        self.bottom_info_label.set_markup(
            "<span color='green'>{}</span>".format(self.info_message)
        )
    else:
        self.bottom_stack.set_visible_child_name("error")
        self.info_message = "{} {} : {}".format(
            _("An error occurred while adding the fonts"), font_names_str, error
        )
        self.bottom_info_label.set_markup(
            "<span color='red'>{}</span>".format(self.info_message)
        )
    self.bottom_revealer.set_reveal_child(True)

    # After adding the font, apply the search filter.
    self.on_search_entry_changed(self.search_entry)


def read_charmaps(filepath):

    def get_charmap(font_path):
        result = subprocess.run(
            ["fc-query", "--format=%{charset}\n", font_path],
            stdout=subprocess.PIPE,
            text=True,
        )

        charmap_raw = result.stdout
        charmap = []

        for range_str in re.findall(
            r"([0-9a-fA-F]+)-?([0-9a-fA-F]+)?", charmap_raw
        ):
            start, end = range_str
            start = int(start, 16)
            end = int(end, 16) if end else start
            for i in range(start, min(end, 0x110000) + 1):
                charmap.append(chr(i))

        return charmap

    font_charmap = get_charmap(filepath)
    return font_charmap
