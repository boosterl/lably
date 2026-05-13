from __future__ import annotations

# Standard library
import gettext
import sys
import threading
from pathlib import Path
from typing import Optional

_ = gettext.gettext

# Third-party
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk  # noqa: E402

# Local
from lably.core.meta import get_author_name, get_version, get_website
from lably.core.printer import PrinterException, print_barcode, print_image
from lably.ui.base_window import BaseMainWindow

APP_ID = "io.github.boosterl.lably"


class GtkMainWindow(BaseMainWindow):
    """GTK4 + Libadwaita implementation of the lably main window."""

    def __init__(self) -> None:
        self._app: Adw.Application = Adw.Application(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._win: Optional[Adw.ApplicationWindow] = None
        self._app.connect("activate", self._on_activate)

    # ------------------------------------------------------------------
    # BaseMainWindow interface
    # ------------------------------------------------------------------

    def show(self) -> None:
        self._app.run(sys.argv)

    def print_file(self) -> None:
        raw = self._selected_file_path
        if not raw:
            self._show_toast(_("No file selected."), error=True)
            return

        file_path = Path(raw)
        reverse = self._file_reverse_row.get_active()
        self._run_in_thread(
            lambda: print_image(file_path, reverse),
            success_msg=_("Printed {name}").format(name=file_path.name),
        )

    def print_barcode(self) -> None:
        buf = self._barcode_text_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).strip()
        if not text:
            self._show_toast(_("Enter some text first."), error=True)
            return

        reverse = self._barcode_reverse_row.get_active()
        self._run_in_thread(
            lambda: print_barcode(text, reverse),
            success_msg=_("Barcode sent to printer."),
        )

    def browse_file(self) -> None:
        dialog = Gtk.FileDialog(title=_("Select a label image"))
        dialog.open(self._win, None, self._on_file_chosen)

    # ------------------------------------------------------------------
    # Application lifecycle
    # ------------------------------------------------------------------

    def _on_activate(self, app: Adw.Application) -> None:
        # Register the bundled icon so the app icon and AboutDialog both
        # resolve APP_ID to our custom SVG.
        _icons_dir = Path(__file__).resolve().parent.parent.parent / "data" / "icons"
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.IconTheme.get_for_display(display).add_search_path(str(_icons_dir))

        self._win = self._build_window(app)
        self._win.present()

    def _build_window(self, app: Adw.Application) -> Adw.ApplicationWindow:
        win = Adw.ApplicationWindow(application=app)
        win.set_title("Lably")
        win.set_default_size(650, 450)

        # ---- Top-level layout ----------------------------------------
        toolbar_view = Adw.ToolbarView()

        # ---- Header bar ----------------------------------------------
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # Print button — outermost left of the header bar
        self._print_btn = Gtk.Button()
        self._print_btn.set_tooltip_text(_("Print"))
        self._print_btn.add_css_class("suggested-action")
        self._print_btn.set_sensitive(False)
        self._print_btn.connect("clicked", lambda _: self._on_print_clicked())

        # Icon + label side by side inside the button (normal state)
        self._print_btn_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._print_btn_content.append(Gtk.Image.new_from_icon_name("printer-symbolic"))
        self._print_btn_content.append(Gtk.Label(label=_("Print")))
        self._print_btn.set_child(self._print_btn_content)

        # Spinner shown while printing
        self._print_btn_spinner = Gtk.Spinner()

        header.pack_start(self._print_btn)

        # "Open file" button in the header start — only visible on file tab
        self._open_btn = Gtk.Button()
        self._open_btn.set_icon_name("folder-open-symbolic")
        self._open_btn.set_tooltip_text(_("Open label image…"))
        self._open_btn.add_css_class("flat")
        self._open_btn.connect("clicked", lambda _: self.browse_file())
        header.pack_start(self._open_btn)

        # ViewSwitcherTitle as the centre title widget.
        # When the window is wide it renders the inline tab switcher;
        # when the window is narrow it collapses to just the app title
        # and raises its "title-visible" property so the bottom bar
        # knows to show itself.
        view_switcher_title = Adw.ViewSwitcherTitle()
        view_switcher_title.set_title("Lably")
        header.set_title_widget(view_switcher_title)

        # Hamburger menu button in the header end
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_tooltip_text(_("Main menu"))
        menu_btn.add_css_class("flat")
        menu_btn.set_menu_model(self._build_app_menu())
        header.pack_end(menu_btn)

        # Wire "about" app action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        app.add_action(about_action)

        # ---- View stack (tabs) ---------------------------------------
        self._stack = Adw.ViewStack()
        stack = self._stack
        view_switcher_title.set_stack(stack)

        stack.add_titled_with_icon(
            self._build_file_page(),
            "file",
            _("File"),
            "document-open-symbolic",
        )
        stack.add_titled_with_icon(
            self._build_barcode_page(),
            "barcode",
            _("Barcode"),
            "view-list-symbolic",
        )

        # Show/hide the open button depending on the active tab
        stack.connect("notify::visible-child", self._on_stack_page_changed)
        # Set initial visibility (file tab is first)
        self._open_btn.set_visible(True)

        toolbar_view.set_content(stack)

        # ---- Bottom navigation bar (narrow / mobile mode) ------------
        # Adw.ViewSwitcherBar is visible only when ViewSwitcherTitle has
        # collapsed (i.e. its "title-visible" property is True), which
        # happens when the window is too narrow to display the inline tabs.
        view_switcher_bar = Adw.ViewSwitcherBar()
        view_switcher_bar.set_stack(stack)
        # Bind bar reveal to the title widget's title-visible property so
        # the bottom bar appears automatically when the header tabs hide.
        view_switcher_title.bind_property(
            "title-visible",
            view_switcher_bar,
            "reveal",
            GObject.BindingFlags.SYNC_CREATE,
        )
        toolbar_view.add_bottom_bar(view_switcher_bar)

        # ---- Toast overlay -------------------------------------------
        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_child(toolbar_view)

        win.set_content(self._toast_overlay)
        return win

    # ------------------------------------------------------------------
    # Page builders
    # ------------------------------------------------------------------

    def _build_file_page(self) -> Gtk.Widget:
        """Build the 'Print File' tab content."""
        # Track which file is currently selected (full path string or None)
        self._selected_file_path: Optional[str] = None

        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(box)

        # --- File preview card (hidden until a file is chosen) --------
        # Use a Gtk.Frame (card style) + plain Gtk.Box so the thumbnail and
        # labels sit truly flush with no Adw.PreferencesRow column offsets.
        self._file_preview_card = Gtk.Frame()
        self._file_preview_card.add_css_class("card")
        self._file_preview_card.set_visible(False)
        box.append(self._file_preview_card)

        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_box.set_margin_top(10)
        row_box.set_margin_bottom(10)
        row_box.set_margin_start(12)
        row_box.set_margin_end(12)
        self._file_preview_card.set_child(row_box)

        # Thumbnail on the left. Gtk.Image respects pixel-size exactly and
        # never expands, unlike Gtk.Picture which tries to fill its allocation.
        self._thumbnail = Gtk.Image()
        self._thumbnail.set_pixel_size(80)
        self._thumbnail.set_hexpand(False)
        self._thumbnail.set_halign(Gtk.Align.START)
        self._thumbnail.set_valign(Gtk.Align.CENTER)
        self._thumbnail.add_css_class("rounded")
        row_box.append(self._thumbnail)

        # Text labels directly to the right of the thumbnail.
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)
        text_box.set_valign(Gtk.Align.CENTER)
        row_box.append(text_box)

        self._preview_name_label = Gtk.Label()
        self._preview_name_label.set_halign(Gtk.Align.START)
        self._preview_name_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self._preview_name_label.add_css_class("body")
        text_box.append(self._preview_name_label)

        self._preview_subtitle_label = Gtk.Label()
        self._preview_subtitle_label.set_halign(Gtk.Align.START)
        self._preview_subtitle_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self._preview_subtitle_label.add_css_class("caption")
        self._preview_subtitle_label.add_css_class("dim-label")
        text_box.append(self._preview_subtitle_label)

        # --- Options group -------------------------------------------
        options_group = Adw.PreferencesGroup()
        options_group.set_title(_("Options"))
        box.append(options_group)

        self._file_reverse_row = Adw.SwitchRow()
        self._file_reverse_row.set_title(_("Reverse"))
        self._file_reverse_row.set_subtitle(_("Mirror the image before printing."))
        options_group.add(self._file_reverse_row)

        return clamp

    def _build_barcode_page(self) -> Gtk.Widget:
        """Build the 'Print Barcode' tab content."""
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(box)

        # --- Text entry group ----------------------------------------
        text_group = Adw.PreferencesGroup()
        text_group.set_title(_("Barcode Text"))
        text_group.set_description(_("Enter the text to encode as a Code 128 barcode."))
        box.append(text_group)

        text_row = Adw.ActionRow()
        text_row.set_title(_("Text"))
        text_row.set_activatable(False)
        text_group.add(text_row)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(100)

        self._barcode_text_view = Gtk.TextView()
        self._barcode_text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._barcode_text_view.add_css_class("monospace")
        self._barcode_text_view.set_left_margin(8)
        self._barcode_text_view.set_right_margin(8)
        self._barcode_text_view.set_top_margin(8)
        self._barcode_text_view.set_bottom_margin(8)
        scroll.set_child(self._barcode_text_view)
        text_row.set_child(scroll)

        # Re-evaluate print button whenever the text changes
        self._barcode_text_view.get_buffer().connect(
            "changed", lambda _buf: self._update_print_btn_sensitivity()
        )

        # --- Options group -------------------------------------------
        options_group = Adw.PreferencesGroup()
        options_group.set_title(_("Options"))
        box.append(options_group)

        self._barcode_reverse_row = Adw.SwitchRow()
        self._barcode_reverse_row.set_title(_("Reverse"))
        self._barcode_reverse_row.set_subtitle(_("Mirror the barcode before printing."))
        options_group.add(self._barcode_reverse_row)

        return clamp

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_app_menu(self) -> Gio.Menu:
        menu = Gio.Menu()
        menu.append(_("About Lably"), "app.about")
        return menu

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_stack_page_changed(self, stack: Adw.ViewStack, _param: object) -> None:
        """Show the open-file button only when the file tab is active."""
        page = stack.get_visible_child_name()
        self._open_btn.set_visible(page == "file")
        self._update_print_btn_sensitivity()

    def _on_file_chosen(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
    ) -> None:
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            return

        if gfile is None:
            return

        path = gfile.get_path()
        if not path:
            return

        self._selected_file_path = path
        p = Path(path)

        # Format file size
        try:
            size_str = self._fmt_size(p.stat().st_size)
        except OSError:
            size_str = "unknown size"

        # Update preview card
        self._preview_name_label.set_text(p.name)
        self._preview_subtitle_label.set_text(f"{p.parent}  ·  {size_str}")

        # Scale image to 80 px via GdkPixbuf and load into Gtk.Image.
        # Gtk.Image.set_pixel_size(80) constrains the display; set_from_pixbuf
        # replaces the content without any layout expansion.
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                path, width=80, height=80, preserve_aspect_ratio=True
            )
            self._thumbnail.set_from_pixbuf(pixbuf)
        except GLib.Error:
            self._thumbnail.clear()

        self._file_preview_card.set_visible(True)
        self._update_print_btn_sensitivity()

    def _on_about(self, _action: Gio.SimpleAction, _param: object) -> None:
        author = get_author_name()
        website = get_website()
        issue_url = website.rstrip("/") + "/issues" if website else ""
        about = Adw.AboutDialog(
            application_name="Lably",
            application_icon=APP_ID,
            developer_name=author,
            version=get_version(),
            website=website,
            issue_url=issue_url,
            license_type=Gtk.License.GPL_3_0,
            developers=[author],
            copyright=f"© {author}",
        )
        about.present(self._win)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _on_print_clicked(self) -> None:
        """Dispatch the print action based on the currently visible tab."""
        self._set_print_btn_loading(True)
        if self._stack.get_visible_child_name() == "file":
            self.print_file()
        else:
            self.print_barcode()

    def _update_print_btn_sensitivity(self) -> None:
        """Enable the header-bar print button only when there is something to print."""
        page = self._stack.get_visible_child_name()
        if page == "file":
            sensitive = bool(self._selected_file_path)
        else:
            buf = self._barcode_text_view.get_buffer()
            text = buf.get_text(
                buf.get_start_iter(), buf.get_end_iter(), False
            ).strip()
            sensitive = bool(text)
        self._print_btn.set_sensitive(sensitive)

    def _set_print_btn_loading(self, loading: bool) -> None:
        """Append/remove the spinner from the print button content."""
        if loading:
            self._print_btn_content.append(self._print_btn_spinner)
            self._print_btn_spinner.start()
            self._print_btn.set_sensitive(False)
        else:
            self._print_btn_spinner.stop()
            self._print_btn_content.remove(self._print_btn_spinner)
            self._update_print_btn_sensitivity()

    @staticmethod
    def _fmt_size(num_bytes: int) -> str:
        """Return a human-readable file size string (e.g. '1.4 MB')."""
        for unit in ("B", "KB", "MB", "GB"):
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0  # type: ignore[assignment]
        return f"{num_bytes:.1f} TB"

    def _run_in_thread(self, fn: callable, success_msg: str) -> None:
        """Run a blocking printer call on a worker thread, report back on the main loop."""

        def _worker() -> None:
            try:
                fn()
                GLib.idle_add(self._set_print_btn_loading, False)
                GLib.idle_add(self._show_toast, success_msg, False)
            except PrinterException as exc:
                GLib.idle_add(self._set_print_btn_loading, False)
                GLib.idle_add(self._show_toast, _("Printer error: {error}").format(error=exc), True)
            except ValueError as exc:
                GLib.idle_add(self._set_print_btn_loading, False)
                GLib.idle_add(self._show_toast, _("Invalid value: {error}").format(error=exc), True)
            except Exception as exc:  # noqa: BLE001
                GLib.idle_add(self._set_print_btn_loading, False)
                GLib.idle_add(self._show_toast, _("Unexpected error: {error}").format(error=exc), True)

        threading.Thread(target=_worker, daemon=True).start()

    def _show_toast(self, message: str, error: bool = False) -> None:
        toast = Adw.Toast(title=message)
        toast.set_timeout(3)
        if error:
            toast.set_button_label(_("Dismiss"))
            toast.connect("button-clicked", lambda t: None)
        self._toast_overlay.add_toast(toast)
