from settings.base import *  # noqa: F401, F403
from settings.conf import config

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('BLOG_DB_NAME', default='blogdb'),
        'USER': config('BLOG_DB_USER', default='bloguser'),
        'PASSWORD': config('BLOG_DB_PASSWORD', default=''),
        'HOST': config('BLOG_DB_HOST', default='localhost'),
        'PORT': config('BLOG_DB_PORT', default='5432'),
    }
}

SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
