import asyncio
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger('apps.blog')


class Command(BaseCommand):
    help = 'Subscribe to Redis comments channel and print incoming events'

    def handle(self, *args, **options) -> None:
        self.stdout.write('Listening for comments on Redis channel "comments"...')
        # Using async Redis client and asyncio for non-blocking I/O;
        # synchronous would block the thread on each message, wasting CPU
        asyncio.run(self._listen())

    async def _listen(self) -> None:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe('comments')
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    self.stdout.write(
                        f"New comment: post={data.get('post_slug')} "
                        f"author={data.get('author_id')} "
                        f"body={data.get('body', '')[:80]}"
                    )
                except Exception:
                    logger.exception('Failed to parse comment event')
