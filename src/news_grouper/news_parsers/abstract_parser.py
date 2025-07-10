"""NewsParser abstract base class for news parsers."""

from abc import ABC, abstractmethod
from datetime import datetime

from news_grouper.models.posts import Post


class NewsParser(ABC):
    """Abstract base class for news parsers.
    >>> class RedditParser(NewsParser):
    ...     name = "Reddit"
    ...     description = "Parser for Reddit posts"
    ...     link_hint = "https://www.reddit.com/r/your_subreddit"
    ...
    ...     def get_posts(self, link: str, from_datetime: datetime, to_datetime: datetime) -> list[Post]:
    ...         pass
    ...
    ...     def check_source_link(self, link: str) -> bool:
    ...         pass
    ...
    >>> [[parser.name, parser.description, parser.link_hint] for parser in NewsParser.get_all_parsers()]
    [['Reddit', 'Parser for Reddit posts', 'https://www.reddit.com/r/your_subreddit']]
    >>> NewsParser.get_parser_by_name("Reddit").name
    'Reddit'
    >>> NewsParser.get_parser_by_name("NonExistentParser")
    Traceback (most recent call last):
        ...
    ValueError: Parser with name 'NonExistentParser' not found
    """

    name: str
    description: str
    link_hint: str

    def __init_subclass__(cls):
        for attr in ["name", "description", "link_hint"]:
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define class attribute '{attr}'")
        names = [parser.name for parser in cls.__subclasses__()]
        if cls.name in names:
            raise ValueError(f"Parser name '{cls.name}' is not unique among subclasses")

    @staticmethod
    @abstractmethod
    def get_posts(
        link: str, from_datetime: datetime, to_datetime: datetime | None
    ) -> list[Post]:
        """Get posts from the source within the specified date range.

        :param link: The link to the source from which to fetch posts.
        :param from_datetime: The start date and time for fetching posts.
        :param to_datetime: The end date and time for fetching posts. If None, fetch posts till the current time.
        :return: A list of posts.
        """
        ...

    @staticmethod
    @abstractmethod
    def check_source_link(link: str) -> bool:
        """Check if the source link is valid.

        :param link: The link to check.
        :return: True if the link is valid, False otherwise.
        """
        ...

    @classmethod
    def get_all_parsers(cls) -> list[type["NewsParser"]]:
        """Get all registered parsers."""

        def collect_subclasses(base_class):
            result = []
            for subclass in base_class.__subclasses__():
                result.append(subclass)
                result.extend(collect_subclasses(subclass))
            return result

        return collect_subclasses(cls)

    @classmethod
    def get_parser_by_name(cls, name: str) -> type["NewsParser"]:
        """Get a parser class by its name.

        :param name: The name of the parser.
        :return: The parser class if found, None otherwise.
        :raises ValueError: If no parser with the given name is found.
        """
        for parser_class in cls.get_all_parsers():
            if parser_class.name == name:
                return parser_class
        raise ValueError(f"Parser with name '{name}' not found")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
