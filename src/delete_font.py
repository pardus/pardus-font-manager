import os
import time
import threading
from threading import Thread
import locale
from ctypes import CDLL


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

import font_charmaps

locale.bindtextdomain('pardus-font-manager', '/usr/share/locale')
locale.textdomain('pardus-font-manager')
_ = locale.gettext


def confirm_delete(self, font_count):
    # Customize the confirmation dialog based on the number of fonts
    number_of_fonts = "fonts" if font_count > 1 else "font"
    question = f"Are you sure you want to delete the selected {number_of_fonts}?"
    secondary_text = "This action cannot be undone."

    dialog = Gtk.MessageDialog(
        transient_for=self.window,
        flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text=question,
    )

    dialog.format_secondary_text(secondary_text)
    response = dialog.run()
    dialog.destroy()

    if response == Gtk.ResponseType.YES:
        # Proceed with deletion
        return True

    return False



def delete_font(self, font_path):
    font_file = font_path
    # print(f"font_file: {font_file}")
    if font_file:
        font_folder = os.path.dirname(font_file)

        GLib.idle_add(self.start_progress_bar, 0)

        os.remove(font_file)

        GLib.idle_add(self.start_progress_bar, 50)

        font_name = os.path.basename(font_file)
        self.info_message = "{}: {}".format(_("Deleted font file:"), font_file)

        # Delete the parent directory if it is empty
        if not os.listdir(font_folder):
            os.rmdir(font_folder)
            # print(f"Deleted empty folder: {font_folder}")

            # Update the progress bar to 80 after deleting the folder
            time.sleep(0.5)
            GLib.idle_add(self.start_progress_bar, 80)

    GLib.idle_add(self.start_progress_bar, 100)


def delete_selected_fonts(self, callback=None):
    if self.operation_in_progress:
        return

    self.operation_in_progress = True
    selection = self.fonts_view.get_selection()
    model, paths = selection.get_selected_rows()

    if not paths:
        self.operation_in_progress = False
        return

    if not confirm_delete(self, len(paths)):
        self.operation_in_progress = False
        return

    deleted_font_names = []

    def delete_fonts_and_update():
        for path in paths:
            treeiter = model.get_iter(path)
            if not treeiter:
                continue

            font_path = model[treeiter][1]
            display_name = model[treeiter][0]
            name, style = display_name[:-1].split(' (')

            try:
                del self.font_charmaps[(name, style)]
            except KeyError:
                pass

            delete_font(self, font_path)
            deleted_font_names.append(display_name)

        self.update_font_cache()
        GLib.idle_add(self.update_fonts_list)
        GLib.idle_add(self.on_search_entry_changed, self.search_entry)

        # After deleting all selected font(s) show font names as a msg
        deleted_fonts_message = ", ".join(deleted_font_names)
        GLib.idle_add(self.show_info, f"Deleted fonts: {deleted_fonts_message}")

        if callback:
            GLib.idle_add(callback)

        self.operation_in_progress = False

    threading.Thread(target=delete_fonts_and_update).start()


def on_key_press_event(self, widget, event):
    selection = self.fonts_view.get_selection()

    if event.keyval == Gdk.KEY_Delete:
        if selection.get_mode() == Gtk.SelectionMode.MULTIPLE:
            # For multi-selected font deletion
            delete_selected_fonts()
        else:
            # For single font deletion
            self.delete_selected_font()

        self.on_font_selected(None)

    # Use CTRL + left mouse click to select fonts
    if event.keyval in [Gdk.KEY_Control_L, Gdk.KEY_Control_R]:
        self.multiple_select_active = True
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)


def on_remove_button_clicked(self, button):
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

    self.make_widgets_insensitive(widgets)
    delete_selected_fonts(
        self,
        callback=lambda: self.make_widgets_sensitive(widgets)
    )
