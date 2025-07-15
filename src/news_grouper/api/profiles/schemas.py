from apiflask import Schema
from apiflask.fields import Integer, String
from apiflask.validators import OneOf

from news_grouper.api.common.schemas import TimestampSchema, pagination_schema


class ProfileInSchema(Schema):
    name = String(required=True)
    description = String(required=True)


class ProfileOutSchema(TimestampSchema, ProfileInSchema):
    id = Integer()


ProfileOutPaginationSchema = pagination_schema(ProfileOutSchema)


class ProfileSortingSchema(Schema):
    sort_by = String(
        load_default="updated",
        validate=OneOf(["name", "created", "updated"]),
    )
    order = String(
        load_default="desc",
        validate=OneOf(["asc", "desc"]),
    )
