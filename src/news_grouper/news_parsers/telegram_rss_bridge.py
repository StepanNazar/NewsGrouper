import logging
from datetime import datetime

import fastfeedparser
import requests
from bs4 import BeautifulSoup

from news_grouper.models.posts import Post
from news_grouper.news_parsers.abstract_parser import NewsParser


class TelegramRSSBridgeParser(NewsParser):
    """
    Parse for Telegram using rss-bridge.org
    """

    name = "Telegram RSS Bridge(rss-bridge.org)"
    description = "Parses public Telegram channels using rss-bridge.org. Only last messages are available. Messages with quotes are not available on rss-bridge.org"
    link_hint = "@channel_name or https://t.me/channel_name"

    @staticmethod
    def get_posts(
        link: str,
        from_datetime: datetime | None = None,
        to_datetime: datetime | None = None,
    ) -> list[Post]:
        """
        Get posts from a Telegram channel using rss-bridge.org.

        :param link: The link to the Telegram channel.
        :param from_datetime: The start date and time for fetching posts. If None, all posts are fetched.
        :param to_datetime: The end date and time for fetching posts. If None, all posts are fetched.
        """
        link = TelegramRSSBridgeParser.convert_link(link)
        feed = fastfeedparser.parse(link)
        posts = []
        for entry in feed["entries"]:
            body = ""
            try:
                body = TelegramRSSBridgeParser.extract_text(
                    entry["content"][0]["value"]
                )
            except Exception as e:
                logging.exception("Error extracting text from entry: %s", e)
            if not body:
                continue
            published_time = datetime.fromisoformat(entry["published"])
            if from_datetime and published_time < from_datetime:
                continue
            if to_datetime and published_time > to_datetime:
                continue
            post = Post(
                title=entry["title"],
                body=body,
                published_time=published_time,
                author=entry["author"],
                link=entry["links"][0]["href"],
            )
            posts.append(post)
        return posts

    @staticmethod
    def check_source_link(link: str) -> bool:
        """Check if the source link is valid."""
        link = TelegramRSSBridgeParser.convert_link(link)
        try:
            response = requests.get(link, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @staticmethod
    def convert_link(link: str) -> str:
        """Convert a Telegram link to the rss-bridge.org format.

        >>> TelegramRSSBridgeParser.convert_link("@channel_name")
        'https://rss-bridge.org/bridge01/?action=display&bridge=TelegramBridge&username=channel_name&format=Atom'
        >>> TelegramRSSBridgeParser.convert_link("channel_name")
        'https://rss-bridge.org/bridge01/?action=display&bridge=TelegramBridge&username=channel_name&format=Atom'
        >>> TelegramRSSBridgeParser.convert_link("https://t.me/channel_name")
        'https://rss-bridge.org/bridge01/?action=display&bridge=TelegramBridge&username=channel_name&format=Atom'
        >>> TelegramRSSBridgeParser.convert_link("t.me/channel_name")
        'https://rss-bridge.org/bridge01/?action=display&bridge=TelegramBridge&username=channel_name&format=Atom'
        """
        for prefix in ["https://t.me/", "t.me/", "http://t.me/", "@"]:
            link = link.removeprefix(prefix)

        return f"https://rss-bridge.org/bridge01/?action=display&bridge=TelegramBridge&username={link}&format=Atom"

    @staticmethod
    def extract_text(content):
        soup = BeautifulSoup(content, features="lxml")
        tags = soup.css.select(".tgme_widget_message_text, blockquote")
        return "\n".join(tag.get_text().strip() for tag in tags)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
