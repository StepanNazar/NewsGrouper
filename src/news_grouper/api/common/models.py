from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import orm as so


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


class TimestampMixin:
    created: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
