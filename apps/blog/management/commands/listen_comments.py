"""
This management command is superseded by the WebSocket consumer (CommentConsumer)
which delivers real-time comment events directly to connected browser clients via
Django Channels. This command is kept as a debugging utility only.
"""
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger('apps.blog')


class Command(BaseCommand):
    help = 'Deprecated: real-time comments are now served via WebSocket (ws/posts/<slug>/comments/). This command is a no-op.'

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.WARNING(
            'listen_comments is deprecated. '
            'Real-time comment events are now delivered via the WebSocket endpoint: '
            'ws://<host>/ws/posts/<slug>/comments/'
        ))
