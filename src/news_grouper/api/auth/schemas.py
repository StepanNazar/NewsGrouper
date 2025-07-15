from apiflask import Schema, validators
from apiflask.fields import Email, Integer, String

from news_grouper.api.common.schemas import TimestampSchema

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class AccessTokenSchema(Schema):
    access_token = String()


class PasswordSchema(Schema):
    password = String(
        required=True,
        validate=validators.Length(min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH),
        metadata={"example": "Pas$word123"},
    )


class LoginSchema(PasswordSchema):
    email = Email(required=True, validate=validators.Email())


class RegisterSchema(LoginSchema):
    first_name = String(required=True)
    last_name = String(required=True)


class WhoAmISchema(TimestampSchema, Schema):
    id = Integer()
    first_name = String()
    last_name = String()
    email = Email()
