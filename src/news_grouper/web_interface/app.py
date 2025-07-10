import json
from datetime import datetime

from apiflask import APIFlask, abort
from flask import render_template

from news_grouper.models.news_source import NewsSource
from news_grouper.models.posts import Post, PostGroup
from news_grouper.models.profiles import Profile
from news_grouper.news_groupers import NewsGrouper
from news_grouper.news_parsers import NewsParser
from news_grouper.web_interface.schemas import (
    GrouperOutSchema,
    NewsInSchema,
    NewsResponseSchema,
    ParserOutSchema,
    PostGroupSchema,
    PostSchema,
    ProfileSchema,
    SourceInSchema,
    SourceOutSchema,
    SwitchProfileSchema,
)

app = APIFlask(__name__)

current_profile: Profile | None = None


@app.route("/")
def index():
    """Serve the main page with a simple UI"""
    return render_template("index.html")


@app.get("/api/parsers")
@app.output(ParserOutSchema(many=True))
def get_parsers():
    """Get a list of available parsers"""
    return NewsParser.get_all_parsers()


@app.get("/api/groupers")
@app.output(GrouperOutSchema(many=True))
def get_groupers():
    """Get a list of available groupers"""
    return NewsGrouper.get_all_groupers()


@app.get("/api/sources")
@app.output(SourceOutSchema(many=True))
def get_sources():
    """Get sources for current profile"""
    return current_profile.news_sources if current_profile else []


@app.post("/api/sources")
@app.input(SourceInSchema)
@app.output(SourceOutSchema)
def create_source(json_data):
    """Add a new source to the current profile"""
    if not current_profile:
        abort(400, message="No profile selected")
    parser_name = json_data.pop("parser_name")
    try:
        parser = NewsParser.get_parser_by_name(parser_name)
    except ValueError:
        abort(400, message=f"Parser {parser_name} not found")
    if not parser.check_source_link(json_data["link"]):
        abort(400, message="Invalid link for this parser")
    source_id = (
        current_profile.news_sources[-1].id + 1 if current_profile.news_sources else 1
    )
    new_source = NewsSource(**json_data, id=source_id, parser=parser)
    current_profile.news_sources.append(new_source)
    current_profile.save()
    return new_source, 201


@app.delete("/api/sources/<int:source_id>")
def delete_source(source_id):
    """Delete a source from the current profile"""
    if not current_profile:
        abort(400, message="No profile selected")
    for i, source in enumerate(current_profile.news_sources):
        if source.id == source_id:
            current_profile.news_sources.pop(i)
            current_profile.save()
            return {}, 204
    abort(404, message="Source not found")


@app.post("/api/profiles")
@app.input(ProfileSchema)
@app.output(ProfileSchema)
def create_profile(json_data):
    """Create a new profile"""
    global current_profile
    new_profile = Profile(**json_data, news_sources=[])
    new_profile.save()
    current_profile = new_profile
    return new_profile, 201


@app.get("/api/current-profile")
@app.output(ProfileSchema)
def get_current_profile():
    """Get the current profile"""
    if not current_profile:
        abort(404, message="No profile selected")
    return current_profile


@app.post("/api/current-profile")
@app.input(SwitchProfileSchema)
@app.output(ProfileSchema)
def switch_profile(json_data):
    """Switch to a different profile"""
    global current_profile
    try:
        current_profile = Profile.load(json_data["profile_path"])
    except FileNotFoundError:
        abort(404, message=f"Profile file {json_data['profile_path']} not found")
    except json.JSONDecodeError:
        abort(400, message=f"Invalid profile file format: {json_data['profile_path']}")
    return current_profile


@app.get("/api/news")
@app.input(NewsInSchema, location="query")
@app.output(NewsResponseSchema)
def get_news(query_data):
    """Get news with the chosen grouper"""
    if not current_profile:
        abort(404, message="No profile selected")
    grouper_name = query_data.get("grouper")
    try:
        grouper = NewsGrouper.get_grouper_by_name(grouper_name)
    except ValueError:
        abort(400, message=f"Grouper {grouper_name} not found")
    if not current_profile.news_sources:
        abort(400, message="No news sources configured for current profile")

    all_posts = []
    from_datetime = datetime.fromisoformat(query_data.get("from_datetime"))
    to_datetime = (
        datetime.fromisoformat(query_data.get("to_datetime"))
        if query_data.get("to_datetime")
        else None
    )
    for source in current_profile.news_sources:
        posts = source.parser.get_posts(source.link, from_datetime, to_datetime)
        all_posts.extend(posts)

    if not all_posts:
        abort(400, message="No posts found from any source")

    grouped_results = grouper.group_posts(all_posts)
    individual_posts = []
    groups = []
    for item in grouped_results:
        if isinstance(item, PostGroup):
            groups.append(PostGroupSchema().dump(item))
        elif isinstance(item, Post):
            individual_posts.append(PostSchema().dump(item))

    return {"post_groups": groups, "posts": individual_posts}


if __name__ == "__main__":
    import webview

    # create_window url parameter also accepts wsgi app but typing is not documented
    webview.create_window("News Grouper", app, maximized=True)  # type: ignore
    webview.start()
