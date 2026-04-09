import os
from decouple import Config, RepositoryEnv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

config = Config(RepositoryEnv(ENV_FILE))

SECRET_KEY: str = config('BLOG_SECRET_KEY')
DEBUG: bool = config('BLOG_DEBUG', default=False, cast=bool)
ALLOWED_HOSTS: list[str] = config('BLOG_ALLOWED_HOSTS', default='localhost').split(',')
REDIS_URL: str = config('BLOG_REDIS_URL', default='redis://localhost:6379/0')
EMAIL_BACKEND: str = config('BLOG_EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL: str = config('BLOG_DEFAULT_FROM_EMAIL', default='noreply@blogapi.com')
