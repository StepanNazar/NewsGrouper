from dataclasses import dataclass

from news_grouper.news_parsers.abstract_parser import NewsParser


@dataclass
class NewsSource:
    id: int
    name: str
    parser: type[NewsParser]
    link: str
