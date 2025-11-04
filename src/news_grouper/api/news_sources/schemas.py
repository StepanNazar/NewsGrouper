from apiflask import Schema
from apiflask.fields import Integer, String
from apiflask.validators import OneOf

from news_grouper.api.common.schemas import TimestampSchema, pagination_schema
from news_grouper.api.news_sources.news_parsers import NewsParser


class ParserOutSchema(Schema):
    name = String()
    description = String()
    link_hint = String()


class SourceOutSchema(TimestampSchema, Schema):
    id = Integer()
    name = String()
    parser_name = String()
    link = String()


class SourceInSchema(Schema):
    name = String(required=True)
    parser_name = String(
        required=True,
        validate=OneOf([parser.name for parser in NewsParser.get_all_parsers()]),
        metadata={"enum": [parser.name for parser in NewsParser.get_all_parsers()]},
    )
    link = String(required=True)


SourceOutPaginationSchema = pagination_schema(SourceOutSchema)


class SourceSortingFilteringSchema(Schema):
    sort_by = String(
        load_default="updated",
        validate=OneOf(["name", "created", "updated"]),
    )
    order = String(
        load_default="desc",
        validate=OneOf(["asc", "desc"]),
    )
    parser_name = String(
        validate=OneOf([parser.name for parser in NewsParser.get_all_parsers()]),
        metadata={"enum": [parser.name for parser in NewsParser.get_all_parsers()]},
    )
