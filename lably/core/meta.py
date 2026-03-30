from __future__ import annotations

# Standard library
import re
from importlib.metadata import metadata, PackageNotFoundError

_PACKAGE = "lably"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_meta() -> dict[str, str]:
    """Return the raw importlib.metadata mapping for *lably*, or {}."""
    try:
        return metadata(_PACKAGE)  # type: ignore[return-value]
    except PackageNotFoundError:
        return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_version() -> str:
    """Return the installed package version, e.g. ``'0.0.1'``."""
    return _get_meta().get("Version", "unknown")


def get_author_name() -> str:
    """Return the author's display name, e.g. ``'Bram Oosterlynck'``.

    The ``Author-email`` field in PKG-INFO has the form
    ``Name <email@example.com>`` (RFC 5322).  We strip the ``<...>`` part.
    """
    raw = _get_meta().get("Author-email", "")
    # Strip " <email>" suffix if present
    name = re.sub(r"\s*<[^>]*>", "", raw).strip()
    return name if name else raw


def get_website() -> str:
    """Return the project homepage URL."""
    meta = _get_meta()
    # Prefer the ``Home-page`` field; fall back to the first ``Homepage``
    # entry in ``Project-URL`` (format: ``label, url``).
    url = meta.get("Home-page", "")
    if url:
        return url
    for entry in meta.get_all("Project-URL") or []:  # type: ignore[union-attr]
        label, _, link = entry.partition(", ")
        if label.strip().lower() == "homepage":
            return link.strip()
    return ""
