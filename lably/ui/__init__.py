from __future__ import annotations

# Local
from .base_window import BaseMainWindow


def create_main_window() -> BaseMainWindow:
    """Factory that returns the platform-specific main window.

    GTK 4 + Libadwaita is preferred when PyGObject is available;
    Tkinter is used as the fallback.
    """
    try:
        from lably.platforms.gtk4.main_window import GtkMainWindow

        return GtkMainWindow()
    except ImportError:
        from lably.platforms.tk.main_window import TKMainWindow

        return TKMainWindow()
