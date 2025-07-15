from collections.abc import Sequence, Set

from apiflask import Schema
from apiflask.fields import URL, Boolean, DateTime, Integer, Nested
from apiflask.validators import Range


class LocationHeader(Schema):
    """Schema for headers of 201 responses with Location header"""

    location = URL(metadata={"description": "URL of the created resource"})


class TimestampSchema(Schema):
    created = DateTime()
    updated = DateTime()


class PaginationLinksSchema(Schema):
    """Schema for pagination links in the output"""

    self = URL()
    first = URL()
    next = URL()
    prev = URL()
    last = URL()


class PaginationOutSchema(Schema):
    """Schema for pagination output"""

    links = Nested(PaginationLinksSchema)
    has_prev = Boolean()
    has_next = Boolean()
    page = Integer()
    total_pages = Integer()
    items_per_page = Integer()
    total_items = Integer()


def pagination_query_schema(
    default_per_page: int = 20, max_per_page: int = 100
) -> type[Schema]:
    """Create a pagination query schema with specified default per_page and max per_page values."""

    class PaginationQuerySchema(Schema):
        """Schema for pagination query parameters"""

        page = Integer(load_default=1)
        per_page = Integer(
            load_default=default_per_page, validate=Range(min=1, max=max_per_page)
        )

    return PaginationQuerySchema


def merge_schemas(*schemas: type[Schema]) -> type[Schema]:
    """Merge multiple query parameters schemas into one schema."""
    MergedSchema = type("MergedSchema", (*schemas,), {})
    return MergedSchema


def pagination_schema(
    schema: type[Schema], exclude: Sequence[str] | Set[str] | None = None
) -> type[Schema]:
    """Create a pagination schema for the given schema."""

    schema_name = schema.__name__
    if schema_name.endswith("Schema"):
        schema_name = schema_name[:-6]
    schema_name = schema_name + "PaginationSchema"
    NewSchema = type(
        schema_name,
        (PaginationOutSchema,),
        {
            "items": Nested(schema(exclude=exclude) if exclude else schema, many=True),
            "__module__": schema.__module__,
        },
    )
    return NewSchema
