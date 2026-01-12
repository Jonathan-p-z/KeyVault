from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


def apply_style(root: tk.Tk, *, theme: str = "auto") -> str:
    """Apply a consistent ttk style across the app.

    Returns the actual theme used.
    """

    style = ttk.Style(root)

    # Theme
    used_theme = theme
    try:
        if theme == "auto":
            if os.name == "nt" and "vista" in style.theme_names():
                used_theme = "vista"
            else:
                used_theme = "clam"
        style.theme_use(used_theme)
    except tk.TclError:
        used_theme = style.theme_use()

    try:
        base_size = 10 if os.name == "nt" else 10
        family = "Segoe UI" if os.name == "nt" else tkfont.nametofont("TkDefaultFont").cget("family")
        base = (family, base_size)
        strong = (family, base_size, "bold")

        style.configure(".", font=base)
        style.configure("TButton", padding=(12, 7))
        style.configure("Primary.TButton", font=strong, padding=(14, 8))
        style.configure("TLabelframe", padding=(12, 10))
        style.configure("TLabelframe.Label", font=strong)
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=strong)

        style.configure("Muted.TLabel", foreground="#666")
    except Exception:
        pass

    try:
        if sys.platform.startswith("win"):
            root.tk.call("tk", "scaling", 1.0)
    except Exception:
        pass

    return used_theme
