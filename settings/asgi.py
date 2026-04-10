import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from settings.conf import config

ENV_ID = config('BLOG_ENV_ID', default='local')
if ENV_ID == 'prod':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.local')

django_asgi_app = get_asgi_application()

from apps.notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': URLRouter(websocket_urlpatterns),
})
