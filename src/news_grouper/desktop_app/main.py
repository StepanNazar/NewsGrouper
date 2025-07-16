import sys

if len(sys.argv) == 2:
    # if venv interpreter is passed, restart the script with it
    import subprocess

    subprocess.Popen([sys.argv[1], __file__]).wait()  # noqa: S603
    sys.exit(0)

import datetime
import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

import webview
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_migrate import upgrade
from pyshortcuts import make_shortcut
from webview.dom import ManipulationMode

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from news_grouper.api import create_app, db
from news_grouper.api.auth.models import User
from news_grouper.api.config import Config

MIGRATIONS_DIR = os.path.join(Path(__file__).parent.parent.parent.parent, "migrations")
ALEMBIC_CONFIG_PATH = os.path.join(MIGRATIONS_DIR, "alembic.ini")


def is_db_at_latest_migration():
    alembic_cfg = AlembicConfig(ALEMBIC_CONFIG_PATH)
    alembic_cfg.set_main_option("script_location", MIGRATIONS_DIR)
    script = ScriptDirectory.from_config(alembic_cfg)
    with db.engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        latest_rev = script.get_current_head()
        return current_rev == latest_rev


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
        icon_path = Path(__file__).parent.parent / "api" / "static" / "icon.ico"
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
    """Add a desktop shortcut button and hide the auth tab"""
    button = window.dom.create_element(
        '<a href="#">Desktop Shortcut</a>',
        parent="nav",
        mode=ManipulationMode.LastChild,
    )
    auth_tab = window.dom.get_element("nav a:first-child")
    if auth_tab:
        auth_tab.hide()
    logged_user_info = window.dom.get_element("#user-info")
    if logged_user_info:
        logged_user_info.style["position"] = "fixed"
        logged_user_info.style["opacity"] = "0"
    button.events.click += create_shortcut


basedir = os.path.abspath(os.path.dirname(__file__))


class DesktopConfig(Config):
    """Configuration for the desktop application."""

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "desktop.db")
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=10**6)
    JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(days=10**6)


class AutoLoginMiddleware:
    """Middleware to handle automatic login for the desktop application."""

    def __init__(self, wsgi_app, flask_app):
        self.app = wsgi_app
        self.flask_app = flask_app
        with flask_app.app_context():
            self.refresh_token = create_refresh_token(identity="1")
            self.access_token = create_access_token(identity="1")

    def __call__(self, environ, start_response):
        if environ["PATH_INFO"] == "/api/refresh":
            status = "200 OK"
            headers = [("Content-Type", "application/json")]
            response = f'{{"access_token": "{self.access_token}"}}'
            response = response.encode("utf-8")
            start_response(status, headers)
            return [response]
        elif "HTTP_AUTHORIZATION" not in environ:
            # add access token to request if not present
            environ["HTTP_AUTHORIZATION"] = f"Bearer {self.access_token}"
        return self.app(environ, start_response)


app = create_app(DesktopConfig)
app.wsgi_app = AutoLoginMiddleware(app.wsgi_app, app)

with app.app_context():
    if not is_db_at_latest_migration():
        upgrade(directory=MIGRATIONS_DIR)

    # ensure there is a user in the database
    if not db.session.get(User, 1):
        user = User(
            id=1,
            first_name="User",
            last_name="",
            email="",
            password="Pas$word123",  # noqa: S106
        )
        db.session.add(user)
        db.session.commit()

# create_window url parameter also accepts wsgi app, but typing is not documented
window = webview.create_window("News Grouper", app, maximized=True, text_select=True)  # type: ignore

webview.start(
    bind,
    [window],
    icon="../api/static/icon.ico",
    storage_path=os.path.join(os.path.dirname(__file__), "storage"),
)
