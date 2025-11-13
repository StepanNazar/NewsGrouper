import calendar
import logging
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

from news_grouper.api.common.models import Post
from news_grouper.api.news_sources.news_parsers.abstract_parser import NewsParser


class RSSFeedParser(NewsParser):
    """
    Parser for RSS feeds.
    """

    name = "RSS Feed"
    description = "Parses RSS feeds from various sources. Supports RSS 0.9x, RSS 1.0, RSS 2.0, CDF, Atom 0.3, and Atom 1.0 feeds"
    link_hint = "RSS feed URL"

    @classmethod
    def get_posts(
        cls,
        link: str,
        from_datetime: datetime,
        to_datetime: datetime | None = None,
    ) -> list[Post]:
        """Get posts from an RSS feed within the specified date range.

        :param link: The link to the RSS feed.
        :param from_datetime: The start date and time for fetching posts.
        :param to_datetime: The end date and time for fetching posts. If None, fetch posts till the current time.
        :return: A list of Post objects containing the parsed posts.
        """
        feed = feedparser.parse(link)
        posts = []
        for entry in feed.entries:
            body = cls.extract_body(entry)
            if not body:
                continue
            published_time = cls.extract_published_time(entry)
            if published_time < from_datetime:
                continue
            if to_datetime and published_time > to_datetime:
                continue
            post = Post(
                title=cls.extract_title(entry),
                body=body,
                published_time=published_time,
                author=cls.extract_author(feed, entry),
                link=cls.extract_link(entry),
            )
            posts.append(post)
        return posts

    @classmethod
    def extract_link(cls, entry):
        return entry.link

    @classmethod
    def extract_author(cls, feed, entry):
        return feed.feed.title

    @classmethod
    def extract_published_time(cls, entry):
        struct_time = entry.published_parsed
        return datetime.fromtimestamp(calendar.timegm(struct_time), tz=timezone.utc)

    @classmethod
    def extract_title(cls, entry):
        return entry.title

    @classmethod
    def extract_body(cls, entry):
        body = entry.content[0].value if "content" in entry else entry.description
        try:
            body = cls.extract_text(body)
        except Exception as e:
            logging.exception("Error extracting text from entry: %s", e)
        return body

    @classmethod
    def check_source_link(cls, link: str) -> bool:
        """Check if the source link is valid."""
        try:
            response = requests.get(
                link, timeout=10, headers={"User-Agent": "News Grouper"}
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    @classmethod
    def extract_text(cls, content):
        soup = BeautifulSoup(content, features="lxml")
        for br in soup.find_all("br"):
            br.replace_with(soup.new_string("\n"))
        for p in soup.find_all("p"):
            p.append(soup.new_string("\n"))  # type: ignore
        return soup.get_text().strip()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
