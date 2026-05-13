from __future__ import annotations

# Standard library
import gettext
from pathlib import Path

DOMAIN = "lably"

# Locale directories searched in priority order:
#   1. Bundled inside the installed package  (development / pip install)
#   2. /app/share/locale                     (Flatpak runtime)
#   3. /usr/local/share/locale               (local system install)
#   4. /usr/share/locale                     (system package install)
_LOCALE_DIRS = [
    Path(__file__).resolve().parent.parent / "locale",
    Path("/app/share/locale"),
    Path("/usr/local/share/locale"),
    Path("/usr/share/locale"),
]


def setup_i18n() -> None:
    """Configure gettext for the *lably* text domain.

    Searches for compiled message catalogues (.mo files) in the bundled
    ``lably/locale/`` directory first, then standard system paths, so the
    application works both when run from source and when installed via
    Flatpak or a system package.

    Must be called once, as early as possible in ``__main__``, before any
    module-level ``_ = gettext.gettext`` assignments take effect for
    translated strings to resolve correctly.
    """
    for locale_dir in _LOCALE_DIRS:
        if locale_dir.is_dir():
            gettext.bindtextdomain(DOMAIN, str(locale_dir))
            break
    gettext.textdomain(DOMAIN)
