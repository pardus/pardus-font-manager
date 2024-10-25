import os
import locale
from gi.repository import Gtk, Gdk, GLib

import font_charmaps

locale.bindtextdomain('pardus-font-manager', '/usr/share/locale')
locale.textdomain('pardus-font-manager')
_ = locale.gettext


def confirm_delete(self, font_count):
    if self.operation_in_progress:
        return False

    number_of_fonts = _("fonts") if font_count > 1 else _("font")
    question = _("Are you sure you want to delete the selected {}?").format(number_of_fonts)
    secondary_text = _("This action cannot be undone.")

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

    return response == Gtk.ResponseType.YES


def delete_font(self, font_path):
    """Delete a single font file and its empty parent directory."""
    if not font_path or not os.path.exists(font_path):
        return False

    try:
        font_folder = os.path.dirname(font_path)
        os.remove(font_path)

        if os.path.exists(font_folder) and not os.listdir(font_folder):
            os.rmdir(font_folder)
        return True

    except Exception as e:
        print(f"Error deleting font {font_path}: {e}")
        return False


def process_next_font(self, paths, model, current_index, deleted_font_names, widgets):
    """Process one font at a time using GLib.idle_add"""
    if not paths:
        if widgets:
            self.make_widgets_sensitive(widgets)
        self.operation_in_progress = False
        # Ensure progress bar completes when no paths
        GLib.idle_add(self.start_progress_bar, 100)
        return False

    # Progress update with GLib.idle_add
    progress = int((current_index / len(paths)) * 100)
    GLib.idle_add(self.start_progress_bar, progress)

    # Check if we're done processing all fonts
    if current_index >= len(paths):
        if deleted_font_names:
            last_deleted_index = paths[-1].get_indices()[0]

            self.update_font_cache()
            self.update_fonts_list()
            self.on_search_entry_changed(self.search_entry)

            if len(self.fonts_list) > 0:
                selection = self.fonts_view.get_selection()
                next_index = min(last_deleted_index, len(self.fonts_list) - 1)

                iter_at_index = self.fonts_list.get_iter_from_string(str(next_index))
                if iter_at_index:
                    selection.select_iter(iter_at_index)
                    path = self.fonts_list.get_path(iter_at_index)
                    self.fonts_view.scroll_to_cell(path, None, True, 0.5, 0.5)

            deleted_fonts_message = ", ".join(deleted_font_names)
            self.show_info(_("Deleted fonts: {}").format(deleted_fonts_message))

        # Reset state and re-enable widgets
        self.operation_in_progress = False
        if widgets:
            self.make_widgets_sensitive(widgets)

        # Update font view and complete progress bar
        GLib.idle_add(self.update_font_view)
        GLib.idle_add(self.start_progress_bar, 100)
        return False

    try:
        treeiter = model.get_iter(paths[current_index])
        if not treeiter:
            return False

        font_path = model[treeiter][1]
        display_name = model[treeiter][0]
        name, style = display_name[:-1].split(' (')

        try:
            del self.font_charmaps[(name, style)]
        except KeyError:
            pass

        if delete_font(self, font_path):
            deleted_font_names.append(display_name)

            progress_upt = progress + (100 // len(paths)) // 2
            GLib.idle_add(self.start_progress_bar, progress_upt)

    except Exception as e:
        print(f"Error processing font at index {current_index}: {e}")
        self.show_error(_("Error processing font: {}").format(str(e)))
        self.operation_in_progress = False
        if widgets:
            self.make_widgets_sensitive(widgets)
        # Ensure progress bar completes even on error
        GLib.idle_add(self.start_progress_bar, 100)
        return False

    # Schedule next font processing
    GLib.idle_add(
        process_next_font,
        self, paths, model, current_index + 1,
        deleted_font_names, widgets
    )
    return False


def delete_selected_fonts(self, model, paths, widgets=None):
    """Begin font deletion process."""
    if self.operation_in_progress:
        return

    self.operation_in_progress = True

    GLib.idle_add(self.start_progress_bar, 0)
    GLib.idle_add(
        process_next_font,
        self, paths, model, 0, [], widgets
    )


def on_key_press_event(widget, event, self):
    """Handle keyboard events for font deletion."""
    if event.keyval == Gdk.KEY_Delete:
        on_remove_button_clicked(self, None)
    elif event.keyval in [Gdk.KEY_Control_L, Gdk.KEY_Control_R]:
        self.multiple_select_active = True
        self.fonts_view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)


def on_remove_button_clicked(self, button):
    selection = self.fonts_view.get_selection()
    model, paths = selection.get_selected_rows()

    if not paths:
        return

    if not confirm_delete(self, len(paths)):
        return

    selected_paths = [path.copy() for path in paths]

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
    delete_selected_fonts(self, model, selected_paths, widgets)
