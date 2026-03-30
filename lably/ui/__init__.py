from __future__ import annotations

# Standard library
import os

# Local
from .base_window import BaseMainWindow

_PLATFORM_ENV = "LABLY_PLATFORM"
_DEFAULT_PLATFORM = "tk"


def create_main_window() -> BaseMainWindow:
    """Factory that returns the platform-specific main window.

    The platform is selected via the ``LABLY_PLATFORM`` environment variable.
    Supported values:

    * ``tk``   – Tkinter (default, always available)
    * ``gtk4`` – GTK 4 + Libadwaita (requires PyGObject)
    """
    platform = os.environ.get(_PLATFORM_ENV, _DEFAULT_PLATFORM).lower().strip()

    if platform == "gtk4":
        from lably.platforms.gtk4.main_window import GtkMainWindow

        return GtkMainWindow()

    if platform == "tk":
        from lably.platforms.tk.main_window import TKMainWindow

        return TKMainWindow()

    raise ValueError(
        f"Unknown platform {platform!r}. "
        f"Set {_PLATFORM_ENV} to 'tk' or 'gtk4'."
    )
