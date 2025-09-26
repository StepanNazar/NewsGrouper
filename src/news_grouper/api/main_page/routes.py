from apiflask import APIBlueprint
from flask import render_template

main_page = APIBlueprint("main_page", __name__, url_prefix="/", tag="Main")


@main_page.route("/")
def index():
    """Serve the main page with UI"""
    return render_template("index.html")
