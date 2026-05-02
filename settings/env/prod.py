from settings.base import *  # noqa: F401, F403
from settings.conf import config

DEBUG = False
ALLOWED_HOSTS = config('BLOG_ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db' / 'db.sqlite3',
        # 'USER': config('BLOG_DB_USER', default='bloguser'),
        # 'PASSWORD': config('BLOG_DB_PASSWORD', default=''),
        # 'HOST': config('BLOG_DB_HOST', default='localhost'),
        # 'PORT': config('BLOG_DB_PORT', default='5432'),
    }
}

# SECURE_HSTS_SECONDS = 31536000
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
