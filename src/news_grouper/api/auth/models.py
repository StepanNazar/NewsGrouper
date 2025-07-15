import re

import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import check_password_hash, generate_password_hash

from news_grouper.api import db
from news_grouper.api.common.models import TimestampMixin
from news_grouper.api.profiles.models import Profile


class User(TimestampMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    first_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    last_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256))
    profiles: so.Mapped[list[Profile]] = so.relationship(
        foreign_keys=[Profile.user_id], back_populates="user"
    )

    @classmethod
    def find_by_email(cls, email: str) -> "User | None":
        return cls.query.filter_by(email=email).one_or_none()

    def __init__(self, password: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_password(password)

    def __repr__(self):
        return (
            f"User(id={self.id!r}, email={self.email!r}, "
            f"first_name={self.first_name!r}, last_name={self.last_name!r})"
        )

    def set_password(self, password: str) -> None:
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\W", password):
            raise ValueError("Password must contain at least one special character")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not isinstance(password, str):
            return False
        return check_password_hash(self.password_hash, password)
