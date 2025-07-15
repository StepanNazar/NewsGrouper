from apiflask import APIBlueprint
from flask import url_for
from flask_jwt_extended import get_jwt_identity, jwt_required

from news_grouper.api import db
from news_grouper.api.common.routes import create_pagination_response
from news_grouper.api.common.schemas import (
    LocationHeader,
    merge_schemas,
    pagination_query_schema,
)
from news_grouper.api.profiles.models import Profile
from news_grouper.api.profiles.schemas import (
    ProfileInSchema,
    ProfileOutPaginationSchema,
    ProfileOutSchema,
    ProfileSortingSchema,
)

profiles = APIBlueprint("profiles", __name__, url_prefix="/api", tag="Profiles")


@profiles.get("/profiles")
@jwt_required()
@profiles.input(
    merge_schemas(pagination_query_schema(), ProfileSortingSchema), location="query"
)
@profiles.output(ProfileOutPaginationSchema)
@profiles.doc(security=["jwt_access_token"])
def get_profiles(query_data):
    """Get all profiles"""
    user_id = get_jwt_identity()
    ordering = getattr(Profile, query_data.get("sort_by"))
    if query_data.get("order") == "desc":
        ordering = ordering.desc()
    pagination = Profile.query.filter_by(user_id=user_id).order_by(ordering).paginate()
    return create_pagination_response(pagination, "profiles.get_profiles", **query_data)


@profiles.post("/profiles")
@jwt_required()
@profiles.input(ProfileInSchema)
@profiles.output(ProfileInSchema, status_code=201, headers=LocationHeader)
@profiles.doc(security=["jwt_access_token"])
def create_profile(json_data):
    """Create a new profile"""
    user_id = get_jwt_identity()
    new_profile = Profile(user_id=user_id, **json_data)  # type: ignore
    db.session.add(new_profile)
    db.session.commit()
    headers = {"Location": url_for("profiles.get_profile", profile_id=new_profile.id)}
    return new_profile, 201, headers


@profiles.get("/profiles/<int:profile_id>")
@jwt_required()
@profiles.output(ProfileOutSchema)
@profiles.doc(security=["jwt_access_token"])
def get_profile(profile_id):
    """Get a profile by ID"""
    user_id = get_jwt_identity()
    return Profile.query.filter_by(id=profile_id, user_id=user_id).first_or_404()


@profiles.put("/profiles/<int:profile_id>")
@jwt_required()
@profiles.input(ProfileInSchema)
@profiles.output(ProfileOutSchema)
@profiles.doc(security=["jwt_access_token"])
def update_profile(profile_id, json_data):
    """Update a profile by ID"""
    user_id = get_jwt_identity()
    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first_or_404()
    for key, value in json_data.items():
        setattr(profile, key, value)
    db.session.commit()
    return profile


@profiles.delete("/profiles/<int:profile_id>")
@jwt_required()
@profiles.doc(
    security=["jwt_access_token"], responses={204: {"description": "Profile deleted"}}
)
def delete_profile(profile_id):
    """Delete a profile by ID"""
    user_id = get_jwt_identity()
    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first_or_404()
    db.session.delete(profile)
    db.session.commit()
    return "", 204
