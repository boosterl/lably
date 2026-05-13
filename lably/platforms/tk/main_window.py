from __future__ import annotations

# Standard library
import gettext
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

_ = gettext.gettext

# Local
from lably.core.meta import get_author_name, get_version, get_website
from lably.core.printer import print_image, print_barcode, PrinterException
from lably.ui.base_window import BaseMainWindow


class TKMainWindow(BaseMainWindow):
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(_("Lably"))

        # ---- Menu bar ------------------------------------------------
        menubar = tk.Menu(self.root)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=_("About"), command=self._show_about)
        menubar.add_cascade(label=_("Help"), menu=help_menu)

        self.root.config(menu=menubar)

        # ---- Tabbed interface ----------------------------------------
        notebook = ttk.Notebook(self.root)
        notebook.pack(pady=10, expand=True, fill="both")

        # File Picker Tab
        file_tab = ttk.Frame(notebook)
        notebook.add(file_tab, text=_("File Picker"))

        self.file_path_var = tk.StringVar()
        self.reverse_image = tk.IntVar()
        ttk.Label(file_tab, text=_("Select a file:")).pack(pady=5)
        ttk.Button(file_tab, text=_("Browse…"), command=self.browse_file).pack(pady=5)
        ttk.Entry(file_tab, textvariable=self.file_path_var, width=50).pack(pady=5)
        ttk.Checkbutton(
            file_tab, text=_("Reverse"), variable=self.reverse_image,
            onvalue=1, offvalue=0,
        ).pack(pady=5)
        ttk.Button(file_tab, text=_("Print"), command=self.print_file).pack(pady=5)

        # Text Field Tab
        text_tab = ttk.Frame(notebook)
        notebook.add(text_tab, text=_("Text Field"))

        self.reverse_barcode = tk.IntVar()
        self.text_entry = tk.Text(text_tab, height=10, width=50)
        self.text_entry.pack(pady=5)
        ttk.Checkbutton(
            text_tab, text=_("Reverse"), variable=self.reverse_barcode,
            onvalue=1, offvalue=0,
        ).pack(pady=5)
        ttk.Button(text_tab, text=_("Print"), command=self.print_barcode).pack(pady=5)

    def show(self) -> None:
        self.root.mainloop()

    def print_file(self) -> None:
        file_path = Path(self.file_path_var.get())
        try:
            if file_path:
                print_image(file_path, self.reverse_image.get())
        except PrinterException as ex:
            messagebox.showerror(_("Error Printing"), str(ex))
        except ValueError as ex:
            messagebox.showerror(_("Error Processing"), str(ex))
        except Exception as ex:
            messagebox.showerror(_("Other Issue"), str(ex))

    def print_barcode(self) -> None:
        text = self.text_entry.get("1.0", tk.END).strip()
        if text:
            try:
                print_barcode(text, self.reverse_barcode.get())
            except PrinterException as ex:
                messagebox.showerror(_("Error Printing"), str(ex))
            except ValueError as ex:
                messagebox.showerror(_("Error Processing"), str(ex))
            except Exception as ex:
                messagebox.showerror(_("Other Issue"), str(ex))

    def browse_file(self) -> None:
        filename = filedialog.askopenfilename()
        if filename:
            self.file_path_var.set(filename)

    def _show_about(self) -> None:
        author = get_author_name()
        version = get_version()
        website = get_website()

        win = tk.Toplevel(self.root)
        win.title(_("About Lably"))
        win.resizable(False, False)
        win.grab_set()  # make it modal

        ttk.Label(win, text=_("Lably"), font=("", 16, "bold")).pack(pady=(20, 4))
        ttk.Label(win, text=_("Version {version}").format(version=version)).pack()
        ttk.Label(win, text=_("A GUI for printing labels on DYMO Bluetooth printers.")).pack(
            pady=(8, 0), padx=20,
        )
        ttk.Separator(win, orient="horizontal").pack(fill="x", padx=20, pady=12)
        ttk.Label(win, text=_("Developer")).pack()
        ttk.Label(win, text=author, font=("", 10, "bold")).pack(pady=(2, 0))
        ttk.Label(win, text=website, foreground="gray").pack(pady=(2, 0))
        ttk.Separator(win, orient="horizontal").pack(fill="x", padx=20, pady=12)
        ttk.Label(win, text=f"© {author}  ·  GPL-3.0", foreground="gray").pack(
            pady=(0, 20),
        )

        ttk.Button(win, text=_("Close"), command=win.destroy).pack(pady=(0, 16))
