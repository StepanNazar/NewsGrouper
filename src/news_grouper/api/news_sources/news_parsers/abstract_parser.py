"""NewsParser abstract base class for news parsers."""

from abc import ABC, abstractmethod
from datetime import datetime

from news_grouper.api.common.models import Post
from news_grouper.api.common.subclass_registrar import SubclassRegistrar


class NewsParser(SubclassRegistrar, ABC):
    """Abstract base class for news parsers."""

    name: str
    description: str
    link_hint: str

    @classmethod
    @abstractmethod
    def get_posts(
        cls, link: str, from_datetime: datetime, to_datetime: datetime | None
    ) -> list[Post]:
        """Get posts from the source within the specified date range.

        :param link: The link to the source from which to fetch posts.
        :param from_datetime: The start date and time for fetching posts.
        :param to_datetime: The end date and time for fetching posts. If None, fetch posts till the current time.
        :return: A list of posts.
        """
        ...

    @classmethod
    @abstractmethod
    def check_source_link(cls, link: str) -> bool:
        """Check if the source link is valid.

        :param link: The link to check.
        :return: True if the link is valid, False otherwise.
        """
        ...

    @classmethod
    def get_all_parsers(cls) -> list[type["NewsParser"]]:
        """Get all registered parsers which are not abstract.

        :return: A list of parser classes.
        """
        return cls.get_all_subclasses()

    @classmethod
    def get_parser_by_name(cls, name: str) -> type["NewsParser"]:
        """Get a parser class by its name.

        :param name: The name of the parser.
        :return: The parser class if found, None otherwise.
        :raises ValueError: If no parser with the given name is found.
        """
        return cls.get_subclass_by_name(name)
