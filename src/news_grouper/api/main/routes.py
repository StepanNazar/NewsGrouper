from apiflask import APIBlueprint
from flask import render_template

main = APIBlueprint("main", __name__, url_prefix="/", tag="Main")


@main.route("/")
def index():
    """Serve the main page with UI"""
    return render_template("index.html")
