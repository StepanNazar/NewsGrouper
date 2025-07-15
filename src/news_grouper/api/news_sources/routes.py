from apiflask import APIBlueprint, abort
from flask import url_for
from flask_jwt_extended import get_jwt_identity, jwt_required

from news_grouper.api import db
from news_grouper.api.auth.models import User
from news_grouper.api.common.routes import create_pagination_response
from news_grouper.api.common.schemas import (
    LocationHeader,
    merge_schemas,
    pagination_query_schema,
)
from news_grouper.api.news_sources.models import NewsSource
from news_grouper.api.news_sources.news_parsers import NewsParser
from news_grouper.api.news_sources.schemas import (
    ParserOutSchema,
    SourceInSchema,
    SourceOutPaginationSchema,
    SourceOutSchema,
    SourceSortingFilteringSchema,
)
from news_grouper.api.profiles.models import Profile

sources = APIBlueprint("sources", __name__, url_prefix="/api", tag="Sources")


@sources.get("/parsers")
@sources.output(ParserOutSchema(many=True))
def get_parsers():
    """Get a list of available parsers"""
    return NewsParser.get_all_parsers()


@sources.get("/profiles/<int:profile_id>/sources")
@jwt_required()
@sources.input(
    merge_schemas(pagination_query_schema(), SourceSortingFilteringSchema),
    location="query",
)
@sources.output(SourceOutPaginationSchema)
@sources.doc(security=["jwt_access_token"])
def get_sources(profile_id, query_data):
    """Get sources for current profile"""
    user_id = get_jwt_identity()
    # check if the profile belongs to the user
    Profile.query.filter_by(id=profile_id, user_id=user_id).first_or_404()
    ordering = getattr(NewsSource, query_data.get("sort_by"))
    if query_data.get("order") == "desc":
        ordering = ordering.desc()
    filters = query_data.copy()
    for key in ["sort_by", "order", "page", "per_page"]:
        filters.pop(key)
    pagination = (
        NewsSource.query.filter_by(profile_id=profile_id, **filters)
        .order_by(ordering)
        .paginate()
    )
    return create_pagination_response(
        pagination, "sources.get_sources", profile_id=profile_id, **query_data
    )


@sources.post("/profiles/<int:profile_id>/sources")
@jwt_required()
@sources.input(SourceInSchema)
@sources.output(SourceOutSchema, status_code=201, headers=LocationHeader)
@sources.doc(
    security=["jwt_access_token"], responses={400: "Invalid link for this parser"}
)
def create_source(profile_id, json_data):
    """Add a new source to the current profile"""
    user_id = get_jwt_identity()
    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first_or_404()
    parser = NewsParser.get_parser_by_name(json_data["parser_name"])
    if not parser.check_source_link(json_data["link"]):
        abort(400, message="Invalid link for this parser")
    new_source = NewsSource(**json_data)
    profile.news_sources.append(new_source)
    db.session.commit()
    headers = {"Location": url_for("sources.get_source", source_id=new_source.id)}
    return new_source, 201, headers


@sources.get("/sources/<int:source_id>")
@jwt_required()
@sources.output(SourceOutSchema)
@sources.doc(security=["jwt_access_token"])
def get_source(source_id):
    """Get a source by ID"""
    user_id = get_jwt_identity()
    return NewsSource.query.filter_by(id=source_id, user_id=user_id).first_or_404()


@sources.put("/sources/<int:source_id>")
@jwt_required()
@sources.input(SourceInSchema)
@sources.output(SourceOutSchema)
@sources.doc(
    security=["jwt_access_token"], responses={400: "Invalid link for this parser"}
)
def update_source(source_id, json_data):
    """Update a source in the current profile"""
    user_id = get_jwt_identity()
    source = (
        NewsSource.query.join(NewsSource.profile)
        .join(Profile.user)
        .filter(NewsSource.id == source_id, User.id == user_id)
        .first_or_404()
    )
    parser = NewsParser.get_parser_by_name(json_data["parser_name"])
    if not parser.check_source_link(json_data["link"]):
        abort(400, message="Invalid link for this parser")
    for key, value in json_data.items():
        setattr(source, key, value)
    db.session.commit()
    return source


@sources.delete("/sources/<int:source_id>")
@jwt_required()
@sources.doc(security=["jwt_access_token"], responses={204: "Source deleted"})
def delete_source(source_id):
    """Delete a source from the current profile"""
    user_id = get_jwt_identity()
    source = NewsSource.query.filter_by(id=source_id, user_id=user_id).first_or_404()
    db.session.delete(source)
    db.session.commit()
    return {}, 204
