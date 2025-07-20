import datetime
import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_TRACK_MODIFICATIONS = (
        os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS") or False
    )
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = "Strict"
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(
        minutes=float(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES") or 15)
    )
    JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(
        days=float(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS") or 30)
    )
    JWT_TOKEN_LOCATION = ("cookies", "headers")
    # path to which cookies are sent
    JWT_REFRESH_COOKIE_PATH = "/api/refresh"


class DevConfig(Config):
    # DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_ECHO = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "test.db")


class ProdConfig(Config):
    JWT_COOKIE_SECURE = True
