# AGENTS.md

Guidelines for agentic coding agents working in this repository.

---

## Project Overview

**lably** is a Python 3 desktop GUI application for printing labels on DYMO Bluetooth label printers.
It supports two GUI backends — Tkinter (default) and GTK 4 + Libadwaita — selected at runtime via an
environment variable.

- **Entry point:** `lably/__main__.py` → calls `create_main_window().show()`
- **CLI entry point:** `lably` (installed via `pyproject.toml` scripts)
- **Python version:** 3.8–3.14

---

## Setup

Install in editable/development mode:

```bash
pip install -e .
```

Install development tools (not yet in pyproject.toml, but recommended):

```bash
pip install pytest ruff black mypy
```

To use the GTK 4 backend, install the optional extras (requires GTK 4 and Libadwaita system libraries):

```bash
pip install -e ".[gtk4]"
```

**macOS app bundle only** (not for general use):

```bash
cd lably/
python setup.py py2app
```

---

## Run Commands

```bash
lably                          # Tkinter UI (default)
LABLY_PLATFORM=gtk4 lably      # GTK 4 + Libadwaita UI
python -m lably                # run directly as a module
```

---

## Build / Lint / Test Commands

### Linting

```bash
ruff check .                      # lint entire project
ruff check lably/core/            # lint a specific directory
ruff check lably/core/printer.py  # lint a single file
```

### Formatting

```bash
black .                           # format entire project
black lably/core/printer.py       # format a single file
black --check .                   # check formatting without modifying files
```

### Type Checking

```bash
mypy lably/                       # type-check the package
mypy lably/core/printer.py        # type-check a single file
```

### Testing

> **Note:** The `lably/tests/` directory currently exists but is empty.
> All new tests should be placed there using `pytest`.

```bash
pytest lably/tests/                          # run all tests
pytest lably/tests/test_printer.py           # run a single test file
pytest lably/tests/test_printer.py::test_fn  # run a single test function
pytest -v lably/tests/                       # verbose output
pytest -x lably/tests/                       # stop on first failure
```

---

## Architecture

```
lably/
├── __main__.py               # Entry point
├── core/
│   └── printer.py            # Bluetooth printer logic (async/await + asyncio.run())
├── ui/
│   ├── __init__.py           # Factory: create_main_window() -> BaseMainWindow
│   └── base_window.py        # Abstract base class (ABC + @abstractmethod)
└── platforms/
    ├── tk/
    │   └── main_window.py    # Concrete Tkinter implementation: TKMainWindow
    └── gtk4/
        └── main_window.py    # Concrete GTK 4 + Libadwaita implementation: GtkMainWindow
```

**Key patterns:**
- `BaseMainWindow` (ABC) defines the UI contract; platform implementations subclass it.
- `create_main_window()` reads `LABLY_PLATFORM` (default: `tk`) and returns the matching window.
- Bluetooth printer calls are async; the Tkinter backend uses `asyncio.run()` while the GTK4 backend
  dispatches to a daemon thread and uses `GLib.idle_add()` to report results back on the main loop.

---

## Code Style Guidelines

### General

- Follow **PEP 8** throughout.
- Use **4 spaces** for indentation — never tabs.
- Maximum line length: **88 characters** (black default).
- Use **f-strings** for string formatting; avoid `%` or `.format()`.
- No trailing whitespace; files should end with a single newline.

### Imports

Organize imports in three groups separated by blank lines, in this order:

1. Standard library
2. Third-party packages
3. Local/project imports

```python
# Standard library
import asyncio
from pathlib import Path

# Third-party
from dymo_bluetooth import discover_printers, create_image

# Local
from lably.core.printer import PrinterException
```

- Use **relative imports** within the same package (e.g., `from .base_window import BaseMainWindow`).
- Use **absolute imports** when importing across packages (e.g., `from lably.core.printer import ...`).
- Do not use wildcard imports (`from module import *`).

### Naming Conventions

| Construct | Convention | Example |
|---|---|---|
| Classes | `PascalCase` | `TKMainWindow`, `PrinterException` |
| Functions / methods | `snake_case` | `print_image`, `browse_file` |
| Variables / attributes | `snake_case` | `self.file_path_var`, `input_file` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT` |
| Private members | leading underscore | `_internal_helper` |

### Type Annotations

Add type annotations to all new functions and methods:

```python
def print_image(self, image_path: Path) -> None:
    ...

def create_main_window() -> BaseMainWindow:
    ...
```

- Use `from __future__ import annotations` at the top of files to support forward references.
- Use `Optional[X]` or `X | None` (Python 3.10+) for nullable types.
- Avoid bare `Any`; use specific types wherever possible.

### Error Handling

- Use `PrinterException` (defined in `lably/core/printer.py`) for domain-specific printer errors.
- Always catch specific exceptions before broad ones. Catching bare `Exception` is a last resort.
- All exception branches in UI code should display user-facing messages via `messagebox.showerror()`
  (Tkinter) or `Adw.Toast` (GTK4).
- Be consistent: if one code path handles errors, all sibling code paths should too.

```python
try:
    result = some_operation()
except PrinterException as e:
    messagebox.showerror("Printer Error", str(e))
except ValueError as e:
    messagebox.showerror("Invalid Input", str(e))
except Exception as e:
    messagebox.showerror("Unexpected Error", str(e))
```

- Do not silently swallow exceptions with bare `except: pass`.

### Async Code

- Async logic belongs in `lably/core/`; UI code should remain synchronous.
- Use `asyncio.run()` in UI event handlers to call async core functions.
- Do not use `asyncio.run()` inside an already-running event loop.
- In the GTK4 backend, run blocking printer calls on a `threading.Thread` (daemon) and use
  `GLib.idle_add()` to post results back to the main loop.

---

## Known Issues

- `lably/platforms/tk/__init.py__` has a **malformed filename** (underscores misplaced). It should be renamed to `__init__.py`. This currently prevents the `tk` platform from being properly recognized as a package.
- No `__init__.py` files exist in `lably/core/` or `lably/platforms/` — add them if treating these as explicit packages.
- `print_barcode()` in `TKMainWindow` has no error handling; it should mirror the pattern in `print_file()`.

---

## Dependencies

Runtime (declared in `pyproject.toml`):
- `dymo-bluetooth>=0.1.2` — Bluetooth printer discovery and communication
- `python-barcode>=0.16.1` — Code 128 barcode generation

Optional (declared in `pyproject.toml` under `[project.optional-dependencies]`):
- `PyGObject>=3.42.0` — GTK4/Libadwaita Python bindings (install with `pip install -e ".[gtk4]"`)

Development (install manually until added to `pyproject.toml`):
- `pytest` — testing
- `ruff` — linting
- `black` — formatting
- `mypy` — static type checking
