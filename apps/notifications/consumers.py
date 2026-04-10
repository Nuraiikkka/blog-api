import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger('apps.notifications')


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        slug = self.scope['url_route']['kwargs']['slug']

        token = self._get_token_from_query()
        if not token:
            await self.close(code=4001)
            return

        user = await self._authenticate(token)
        if not user:
            await self.close(code=4001)
            return

        post = await self._get_post(slug)
        if not post:
            await self.close(code=4004)
            return

        self.group_name = f'post_{slug}_comments'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def new_comment(self, event):
        await self.send(text_data=json.dumps(event['message']))

    def _get_token_from_query(self):
        query_string = self.scope.get('query_string', b'').decode()
        for part in query_string.split('&'):
            if part.startswith('token='):
                return part[6:]
        return None

    async def _authenticate(self, token: str):
        try:
            validated = AccessToken(token)
            user_id = validated['user_id']
            return await self._get_user(user_id)
        except Exception:
            return None

    @database_sync_to_async
    def _get_user(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_post(self, slug: str):
        from apps.blog.models import Post
        try:
            return Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return None
