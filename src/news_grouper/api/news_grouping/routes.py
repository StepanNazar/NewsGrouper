from datetime import datetime

from apiflask import APIBlueprint, abort
from flask_jwt_extended import get_jwt_identity, jwt_required

from news_grouper.api import db
from news_grouper.api.auth.models import User
from news_grouper.api.common.models import Post, PostGroup
from news_grouper.api.news_grouping.news_groupers import NewsGrouper
from news_grouper.api.news_grouping.news_groupers.gemini import GeminiClient
from news_grouper.api.news_grouping.schemas import (
    GrouperOutSchema,
    NewsInSchema,
    NewsResponseSchema,
    PostGroupSchema,
    PostSchema,
)
from news_grouper.api.profiles.models import Profile

grouping = APIBlueprint("grouping", __name__, url_prefix="/api", tag="Grouping")


@grouping.get("/groupers")
@grouping.output(GrouperOutSchema(many=True))
def get_groupers():
    """Get a list of available groupers"""
    return NewsGrouper.get_all_groupers()


@grouping.get("/profiles/<int:profile_id>/news")
@jwt_required()
@grouping.input(NewsInSchema, location="query")
@grouping.output(NewsResponseSchema)
@grouping.doc(security=["jwt_access_token"])
def get_news(profile_id, query_data):
    """Get news with the chosen grouper"""
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first_or_404()
    if not profile.news_sources:
        abort(400, message="No news sources configured for current profile")

    all_posts = []
    from_datetime = datetime.fromisoformat(query_data.get("from_datetime"))
    to_datetime = (
        datetime.fromisoformat(query_data.get("to_datetime"))
        if query_data.get("to_datetime")
        else None
    )
    for source in profile.news_sources:
        posts = source.parser.get_posts(source.link, from_datetime, to_datetime)
        all_posts.extend(posts)

    if not all_posts:
        abort(400, message="No posts found from any source")

    gemini_client = GeminiClient(api_key=user.api_key)

    grouper = NewsGrouper.get_grouper_by_name(query_data["grouper"])
    grouped_results = grouper.group_posts(all_posts, gemini_client)
    individual_posts = []
    groups = []
    for item in grouped_results:
        if isinstance(item, PostGroup):
            groups.append(PostGroupSchema().dump(item))
        elif isinstance(item, Post):
            individual_posts.append(PostSchema().dump(item))

    return {"post_groups": groups, "posts": individual_posts}
