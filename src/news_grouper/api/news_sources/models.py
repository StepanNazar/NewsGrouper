from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from flask_sqlalchemy.query import Query
from sqlalchemy import orm as so

from news_grouper.api import db
from news_grouper.api.common.models import TimestampMixin
from news_grouper.api.news_sources.news_parsers import NewsParser

if TYPE_CHECKING:
    from news_grouper.api.profiles.models import Profile


class NewsSource(TimestampMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(256))
    link: so.Mapped[str] = so.mapped_column(sa.Text())
    parser_name: so.Mapped[str] = so.mapped_column(sa.String(256))
    profile_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("profile.id"))
    profile: so.Mapped[Profile] = so.relationship(back_populates="news_sources")

    def __repr__(self):
        return (
            f"NewsSource(id={self.id!r}, name={self.name!r}, link={self.link!r}, "
            f"parser_name={self.parser_name!r}, profile_id={self.profile_id!r})"
        )

    @property
    def parser(self) -> type[NewsParser]:
        return NewsParser.get_parser_by_name(self.parser_name)

    @parser.setter
    def parser(self, parser: type[NewsParser]) -> None:
        if not issubclass(parser, NewsParser):
            raise ValueError("Parser must be a subclass of NewsParser")
        self.parser_name = parser.name

    @classmethod
    def query_users_source(cls, user_id: int, source_id: int) -> Query:
        return cls.query.filter(cls.profile.has(user_id=user_id), cls.id == source_id)
