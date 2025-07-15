from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import orm as so

from news_grouper.api import db
from news_grouper.api.common.models import TimestampMixin
from news_grouper.api.news_sources.models import NewsSource

if TYPE_CHECKING:
    from news_grouper.api.auth.models import User


class Profile(TimestampMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(256))
    description: so.Mapped[str] = so.mapped_column(sa.Text())
    news_sources: so.Mapped[list[NewsSource]] = so.relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    user: so.Mapped[User] = so.relationship(
        foreign_keys=[user_id], back_populates="profiles"
    )

    def __repr__(self):
        return f"Profile(id={self.id!r}, name={self.name!r}, user_id={self.user_id!r})"
