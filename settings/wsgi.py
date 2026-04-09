import os

from django.core.wsgi import get_wsgi_application

from settings.conf import config

ENV_ID = config('BLOG_ENV_ID', default='local')
if ENV_ID == 'prod':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.local')

application = get_wsgi_application()
