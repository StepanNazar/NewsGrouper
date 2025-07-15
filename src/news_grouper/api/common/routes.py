from flask import url_for
from flask_sqlalchemy.pagination import Pagination


def pagination_links(pagination: Pagination, endpoint: str, **kwargs) -> dict:
    """Generate pagination links for the given pagination object and endpoint.

    :param pagination: The pagination object from Flask-SQLAlchemy.
    :param endpoint: The endpoint to generate links for.
    :param kwargs: Additional query parameters to include in the links.
    :return: A dictionary containing pagination links.
    """
    nav_links = {}
    kwargs.pop("page", None)
    kwargs.pop("per_page", None)
    per_page = pagination.per_page
    this_page = pagination.page
    last_page = pagination.pages
    nav_links["self"] = url_for(endpoint, page=this_page, per_page=per_page, **kwargs)
    nav_links["first"] = url_for(endpoint, page=1, per_page=per_page, **kwargs)
    if pagination.has_prev:
        nav_links["prev"] = url_for(
            endpoint, page=pagination.prev_num, per_page=per_page, **kwargs
        )
    if pagination.has_next:
        nav_links["next"] = url_for(
            endpoint, page=pagination.next_num, per_page=per_page, **kwargs
        )
    nav_links["last"] = url_for(endpoint, page=last_page, per_page=per_page, **kwargs)
    return nav_links


def create_pagination_response(pagination: Pagination, endpoint: str, **kwargs) -> dict:
    """Create a pagination response that matches your schema.

    :param pagination: The pagination object from Flask-SQLAlchemy
    :param endpoint: The endpoint to generate links for.
    :param kwargs: Additional query parameters to include in the links.
    :return: A dictionary matching pagination schema
    """
    return {
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
        "items": pagination.items,
        "items_per_page": pagination.per_page,
        "links": pagination_links(pagination, endpoint, **kwargs),
        "page": pagination.page,
        "total_items": pagination.total,
        "total_pages": pagination.pages,
    }
