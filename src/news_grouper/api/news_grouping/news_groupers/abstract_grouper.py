from abc import ABC, abstractmethod
from collections.abc import Iterable

from news_grouper.api.common.models import Post, PostGroup
from news_grouper.api.common.subclass_registrar import SubclassRegistrar
from news_grouper.api.news_grouping.news_groupers.gemini import GeminiClient


class NewsGrouper(SubclassRegistrar, ABC):
    """Abstract base class for news groupers."""

    name: str
    description: str

    @classmethod
    def group_posts(
        cls, posts: list[Post], gemini_client: GeminiClient
    ) -> list[Post | PostGroup]:
        """Group posts based on some criteria.

        :param posts: The list of posts to group.
        :param gemini_client: The Gemini client to use for API calls.
        :return: A list of grouped posts.
        """
        groups = cls._get_groups(posts, gemini_client)
        result = []
        for group_posts in groups:
            if len(group_posts) == 1:
                result.append(group_posts[0])
            else:
                summary = cls.summarize_posts(group_posts, gemini_client)
                result.append(PostGroup(posts=group_posts, summary=summary))
        return result

    @classmethod
    def summarize_posts(cls, posts: list[Post], gemini_client: GeminiClient) -> str:
        """Summarize a list of posts. The default implementation uses Gemini API.

        :param posts: The list of posts to summarize.
        :param gemini_client: The Gemini client to use for API calls.
        :return: The summary of the posts.
        """
        return gemini_client.summarize_posts(posts)

    @classmethod
    @abstractmethod
    def _get_groups(
        cls, posts: list[Post], gemini_client: GeminiClient
    ) -> Iterable[list[Post]]:
        """Abstract method to get groups of posts.

        :param posts: The list of posts to group.
        :param gemini_client: The Gemini client to use for API calls.
        :return: A list of groups, where each group is a list of posts.
        """
        ...

    @classmethod
    def get_all_groupers(cls) -> list[type["NewsGrouper"]]:
        """Get all registered news groupers which are not abstract.

        :return: A list of all news grouper classes.
        """
        return cls.get_all_subclasses()

    @classmethod
    def get_grouper_by_name(cls, name: str) -> type["NewsGrouper"]:
        """Get a news grouper class by its name.

        :param name: The name of the grouper.
        :return: The grouper class if found, otherwise None.
        :raises ValueError: If no grouper with the given name is found.
        """
        return cls.get_subclass_by_name(name)
