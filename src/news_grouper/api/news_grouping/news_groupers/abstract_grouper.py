from abc import ABC, abstractmethod

from news_grouper.api.common.models import Post, PostGroup
from news_grouper.api.config import GOOGLE_API_KEY
from news_grouper.api.news_grouping.news_groupers.gemini import GeminiClient


class NewsGrouper(ABC):
    """Abstract base class for news groupers.

    >>> class RedditGrouper(NewsGrouper):
    ...     name = "Reddit"
    ...     description = "Grouper for Reddit posts"
    ...
    ...     def group_posts(self, posts: list[Post]) -> list[Post]:
    ...         pass
    ...
    ...     def check_source_link(self, link: str) -> bool:
    ...         pass
    ...
    >>> [[grouper.name, grouper.description] for grouper in NewsGrouper.get_all_groupers()]
    [['Reddit', 'Grouper for Reddit posts']]
    >>> NewsGrouper.get_grouper_by_name('Reddit').name
    'Reddit'
    >>> NewsGrouper.get_grouper_by_name('NonExistent')
    Traceback (most recent call last):
        ...
    ValueError: Grouper with name 'NonExistent' not found
    """

    name: str
    description: str
    gemini_client: GeminiClient = GeminiClient(api_key=GOOGLE_API_KEY)

    def __init_subclass__(cls):
        for attr in ["name", "description"]:
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define class attribute '{attr}'")
        names = [grouper.name for grouper in cls.__subclasses__()]
        if cls.name in names:
            raise ValueError(
                f"Grouper name '{cls.name}' is not unique among subclasses"
            )

    @classmethod
    def group_posts(cls, posts: list[Post]) -> list[Post | PostGroup]:
        """Group posts based on some criteria.

        :param posts: The list of posts to group.
        :return: A list of grouped posts.
        """
        groups = cls._get_groups(posts)
        result = []
        for group in groups.values():
            if len(group) == 1:
                result.append(posts[group[0]])
            else:
                grouped_posts = [posts[i] for i in group]
                summary = cls.summarize_posts(grouped_posts)
                result.append(PostGroup(posts=grouped_posts, summary=summary))
        return result

    @classmethod
    def summarize_posts(cls, posts: list[Post]) -> str:
        """Summarize a list of posts. The default implementation uses Gemini API.

        :param posts: The list of posts to summarize.
        :return: The summary of the posts.
        """
        return NewsGrouper.gemini_client.summarize_posts(posts)

    @classmethod
    @abstractmethod
    def _get_groups(cls, posts: list[Post]) -> dict[int, list[int]]:
        """Abstract method to get groups of posts.

        :param posts: The list of posts to group.
        :return: A dictionary where keys are group labels and values are lists of posts indices.
        """
        ...

    @classmethod
    def get_all_groupers(cls) -> list[type["NewsGrouper"]]:
        """Get all registered news groupers.

        :return: A list of all news grouper classes.
        """

        def collect_subclasses(base_class):
            result = []
            for subclass in base_class.__subclasses__():
                result.append(subclass)
                result.extend(collect_subclasses(subclass))
            return result

        return collect_subclasses(cls)

    @classmethod
    def get_grouper_by_name(cls, name: str) -> type["NewsGrouper"]:
        """Get a news grouper class by its name.

        :param name: The name of the grouper.
        :return: The grouper class if found, otherwise None.
        :raises ValueError: If no grouper with the given name is found.
        """
        for grouper in cls.get_all_groupers():
            if grouper.name.lower() == name.lower():
                return grouper
        raise ValueError(f"Grouper with name '{name}' not found")
