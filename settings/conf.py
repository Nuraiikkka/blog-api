from decouple import config, RepositoryEnv, Csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

config = Config(RepositoryEnv(BASE_DIR / ".env"))

BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")

SECRET_KEY = config("BLOG_SECRET_KEY", default="unsafe-secret-key")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("BLOG_ALLOWED_HOSTS", default="127.0.0.1, localhost").split(",")

REDIS_URL = config("BLOG_REDIS_URL", default="redis://127.0.0.1:6379/1")

DB_NAME = config("BLOG_DB_NAME", default="")
DB_USER = config("BLOG_DB_USER", default="")
DB_PASSWORD = config("BLOG_DB_PASSWORD", default="")
DB_HOST = config("BLOG_DB_HOST", default="")
DB_PORT = config("BLOG_DB_PORT", default="5432")