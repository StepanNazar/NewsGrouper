from apiflask import Schema
from marshmallow.fields import Integer, List, Nested, String


class ParserOutSchema(Schema):
    name = String()
    description = String()
    link_hint = String()


class GrouperOutSchema(Schema):
    name = String()
    description = String()


class SourceOutSchema(Schema):
    id = Integer()
    name = String()
    parser_name = String(attribute="parser.name")
    link = String()


class SourceInSchema(Schema):
    name = String(required=True)
    parser_name = String(required=True)
    link = String(required=True)


class ProfileSchema(Schema):
    name = String(required=True)
    description = String(required=True)
    file_path = String(required=True)


class SwitchProfileSchema(Schema):
    profile_path = String(required=True)


class NewsInSchema(Schema):
    grouper = String(required=True)
    from_datetime = String()
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
