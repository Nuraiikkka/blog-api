import asyncio
import json
import logging

import redis.asyncio as aioredis
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import StreamingHttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer

logger = logging.getLogger('apps.notifications')

User = get_user_model()


async def post_stream(request):
    """
    SSE endpoint for real-time post publication events.

    SSE is a good fit here because:
    - The data flow is one-directional: server -> client.
    - Posts are published infrequently compared to chat messages.
    - SSE works over plain HTTP/1.1 with automatic reconnect built into the browser.

    When to choose WebSockets instead:
    - When you need bidirectional communication (e.g., chat, collaborative editing).
    - When the client needs to send events back to the server over the same connection.
    """
    async def event_generator():
        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe('post_published')
        try:
            yield 'retry: 5000\n\n'
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    yield f"data: {message['data'].decode()}\n\n"
        finally:
            await pubsub.unsubscribe('post_published')
            await r.aclose()

    response = StreamingHttpResponse(event_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


class NotificationCountView(APIView):
    """
    HTTP polling endpoint returning unread notification count.

    Polling trade-off:
    - Simplicity: No persistent connection, works with any HTTP client, easy to cache and load-balance.
    - Latency: Updates are delayed by the polling interval (e.g., up to N seconds).
    - Server load: Each polling request is a full HTTP roundtrip; at scale, many clients can overload the server.

    Polling is acceptable when:
    - Low-frequency updates are tolerable (e.g., "you have X unread notifications").
    - The client base is small or the polling interval is large (e.g., every 30s).
    - Simplicity of implementation outweighs real-time requirements.

    Switch to WebSockets or SSE when:
    - Sub-second latency is required (e.g., live chat, trading dashboards).
    - The server load from frequent polling becomes unacceptable.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from rest_framework.pagination import PageNumberPagination
        notifications = Notification.objects.filter(recipient=request.user).select_related('comment', 'comment__author', 'comment__post')
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(notifications, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        updated = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'marked_read': updated})
