from apiflask import Schema
from apiflask.fields import List, Nested, String
from apiflask.validators import OneOf

from news_grouper.api.news_grouping.news_groupers import NewsGrouper


class GrouperOutSchema(Schema):
    name = String()
    description = String()


class NewsInSchema(Schema):
    grouper = String(
        required=True,
        validate=OneOf([grouper.name for grouper in NewsGrouper.get_all_groupers()]),
    )
    from_datetime = String(required=True)
    to_datetime = String()


class PostSchema(Schema):
    title = String()
    body = String()
    author = String()
    published_time = String()
    link = String()


class PostGroupSchema(Schema):
    summary = String()
    posts = List(Nested(PostSchema))


class NewsResponseSchema(Schema):
    post_groups = List(Nested(PostGroupSchema))
    posts = List(Nested(PostSchema))
