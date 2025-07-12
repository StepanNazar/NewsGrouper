import sys

if len(sys.argv) == 2:
    # if venv interpreter is passed, restart the script with it
    import subprocess

    subprocess.Popen([sys.argv[1], __file__]).wait()  # noqa: S603
    sys.exit(0)

import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

import webview
from pyshortcuts import make_shortcut
from webview.dom import ManipulationMode

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from news_grouper.api.app import create_app


def create_shortcut(event) -> None:
    """Create a desktop/start menu shortcut"""
    try:
        root = tk.Tk()
        root.withdraw()
        shortcut_name = simpledialog.askstring(
            "Shortcut Name", "Enter shortcut name:", initialvalue="News Grouper"
        )
        if not shortcut_name:
            root.destroy()
            return
        desktop = messagebox.askyesno("Desktop Shortcut", "Create desktop shortcut?")
        start_menu = messagebox.askyesno(
            "Start Menu Shortcut", "Create start menu shortcut?"
        )
        root.destroy()
        if not desktop and not start_menu:
            return

        script = sys.argv[0]
        if not os.path.isabs(script):
            script = os.path.abspath(script)
        if sys.prefix != sys.base_prefix:
            # if running in a virtual environment, pass its interpreter
            script += f" {sys.executable}"
        icon_path = Path(__file__).parent.parent / "api" / "static" / "icon.svg"
        make_shortcut(
            script=script,
            name=shortcut_name,
            description=f"{shortcut_name} Desktop Application",
            icon=str(icon_path),
            desktop=desktop,
            startmenu=start_menu,
            terminal=False,
        )
        messagebox.showinfo("Success", "Shortcuts created successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create shortcuts: {e!s}")


def bind(window: webview.Window) -> None:
    """Bind the window to the webview."""
    button = window.dom.create_element(
        '<a href="#">Desktop Shortcut</a>',
        parent="nav",
        mode=ManipulationMode.LastChild,
    )
    button.events.click += create_shortcut


app = create_app()
# create_window url parameter also accepts wsgi app, but typing is not documented
window = webview.create_window("News Grouper", app, maximized=True, text_select=True)  # type: ignore

webview.start(bind, [window], icon="../api/static/icon.svg")
