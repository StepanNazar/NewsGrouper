from datetime import datetime

from bs4 import BeautifulSoup

from news_grouper.models.posts import Post
from news_grouper.news_parsers import RSSFeedParser


class TelegramRSSBridgeParser(RSSFeedParser):
    """
    Parse for Telegram using rss-bridge.org
    """

    name = "Telegram RSS Bridge(rss-bridge.org)"
    description = "Parses public Telegram channels using rss-bridge.org. Only last messages are available. Messages with quotes are not available on rss-bridge.org"
    link_hint = "@channel_name or https://t.me/channel_name"

    @classmethod
    def get_posts(
        cls,
        link: str,
        from_datetime: datetime,
        to_datetime: datetime | None = None,
    ) -> list[Post]:
        """
        Get posts from a Telegram channel using rss-bridge.org.

        :param link: The link to the Telegram channel.
        :param from_datetime: The start date and time for fetching posts.
        :param to_datetime: The end date and time for fetching posts. If None, fetch posts till the current time.
        """
        link = cls.convert_link(link)
        return super().get_posts(link, from_datetime, to_datetime)

    @classmethod
    def check_source_link(cls, link: str) -> bool:
        """Check if the source link is valid."""
        link = cls.convert_link(link)
        return super().check_source_link(link)

    @classmethod
    def convert_link(cls, link: str) -> str:
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

    @classmethod
    def extract_text(cls, content):
        soup = BeautifulSoup(content, features="lxml")
        for br in soup.find_all("br"):
            br.replace_with(soup.new_string("\n"))
        tags = soup.css.select(".tgme_widget_message_text, blockquote")
        return "\n".join(tag.get_text().strip() for tag in tags)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
