from dataclasses import dataclass
from datetime import datetime


@dataclass
class Post:
    title: str
    body: str
    published_time: datetime
    author: str
    link: str


@dataclass
class PostGroup:
    posts: list[Post]
    summary: str
