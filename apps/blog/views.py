import asyncio
import json
import logging

import httpx
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.blog.constants import PostStatus
from apps.blog.models import Comment, Post
from apps.blog.permissions import IsOwnerOrReadOnly
from apps.blog.serializers import CommentSerializer, PostSerializer

logger = logging.getLogger('apps.blog')

CACHE_KEY_POSTS = 'posts_list'
EXTERNAL_API_EXCHANGE = 'https://open.er-api.com/v6/latest/USD'
EXTERNAL_API_TIME = 'https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty'


def _build_cache_key(request: Request) -> str:
    lang = getattr(request, 'LANGUAGE_CODE', 'en')
    page = request.query_params.get('page', 1)
    return f'{CACHE_KEY_POSTS}_{lang}_page_{page}'


@extend_schema(tags=['Posts'])
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'slug'

    def get_throttles(self):
        if self.action == 'create':
            from apps.blog.throttles import PostCreateRateThrottle
            return [PostCreateRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        if self.action in ('list', 'retrieve', 'comments', 'add_comment'):
            return Post.objects.filter(status=PostStatus.PUBLISHED).select_related('author', 'category').prefetch_related('tags')
        return Post.objects.filter(author=self.request.user).select_related('author', 'category').prefetch_related('tags')

    @extend_schema(
        summary='List published posts',
        description='Returns a paginated list of published posts. Cached per language for 60 seconds. No authentication required.',
        responses={200: PostSerializer(many=True)},
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        cache_key = _build_cache_key(request)
        cached = cache.get(cache_key)
        if cached:
            logger.info('Posts list served from cache, lang=%s', getattr(request, 'LANGUAGE_CODE', 'en'))
            return Response(cached)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            cache.set(cache_key, result.data, timeout=60)
            return result

        serializer = self.get_serializer(queryset, many=True)
        # Use manual cache.set for fine-grained control (cache_page won't work with per-language keys)
        cache.set(cache_key, serializer.data, timeout=60)
        return Response(serializer.data)

    @extend_schema(
        summary='Create a post',
        description='Creates a new blog post. Authentication required. Invalidates the posts list cache. Rate limited to 20 requests per minute per user.',
        request=PostSerializer,
        responses={201: PostSerializer, 400: OpenApiResponse(description='Validation error'), 401: OpenApiResponse(description='Authentication required'), 429: OpenApiResponse(description='Too many requests')},
    )
    def create(self, request: Request, *args, **kwargs) -> Response:
        logger.info('Post creation attempt by user: %s', request.user.email)
        response = super().create(request, *args, **kwargs)
        self._invalidate_posts_cache()
        return response

    @extend_schema(
        summary='Get a single post',
        description='Returns a single published post by slug. No authentication required.',
        responses={200: PostSerializer, 404: OpenApiResponse(description='Not found')},
    )
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Update own post',
        description='Partially updates the authenticated user\'s post. Authentication required.',
        request=PostSerializer,
        responses={200: PostSerializer, 403: OpenApiResponse(description='Forbidden'), 404: OpenApiResponse(description='Not found')},
    )
    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        logger.info('Post update attempt: %s by %s', kwargs.get('slug'), request.user.email)
        response = super().partial_update(request, *args, **kwargs)
        self._invalidate_posts_cache()
        return response

    @extend_schema(
        summary='Delete own post',
        description='Deletes the authenticated user\'s post. Authentication required.',
        responses={204: None, 403: OpenApiResponse(description='Forbidden'), 404: OpenApiResponse(description='Not found')},
    )
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        logger.info('Post delete attempt: %s by %s', kwargs.get('slug'), request.user.email)
        response = super().destroy(request, *args, **kwargs)
        self._invalidate_posts_cache()
        return response

    def _invalidate_posts_cache(self) -> None:
        from apps.users.constants import SUPPORTED_LANGUAGES
        for lang in SUPPORTED_LANGUAGES:
            for page in range(1, 20):
                cache.delete(f'{CACHE_KEY_POSTS}_{lang}_page_{page}')
        logger.info('Posts list cache invalidated')

    @extend_schema(
        summary='List comments for a post',
        description='Returns all comments for the given post. No authentication required.',
        responses={200: CommentSerializer(many=True), 404: OpenApiResponse(description='Post not found')},
        tags=['Comments'],
    )
    @action(detail=True, methods=['get'], url_path='comments')
    def comments(self, request: Request, slug: str = None) -> Response:
        post = self.get_object()
        comments = Comment.objects.filter(post=post).select_related('author')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary='Add a comment to a post',
        description='Adds a comment to the given post. Authentication required. Publishes a Redis event to the "comments" channel.',
        request=CommentSerializer,
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Post not found'),
        },
        tags=['Comments'],
    )
    @action(detail=True, methods=['post'], url_path='comment', permission_classes=[IsAuthenticated])
    def add_comment(self, request: Request, slug: str = None) -> Response:
        post = self.get_object()
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        comment = serializer.save(post=post, author=request.user)
        logger.info('Comment added to post %s by %s', post.slug, request.user.email)

        self._publish_comment_event(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _publish_comment_event(self, comment: Comment) -> None:
        import redis as redis_client
        from django.conf import settings
        try:
            r = redis_client.from_url(settings.REDIS_URL)
            event = json.dumps({
                'post_slug': comment.post.slug,
                'author_id': comment.author.id,
                'body': comment.body,
            })
            r.publish('comments', event)
            logger.info('Comment event published for post %s', comment.post.slug)
        except Exception:
            logger.exception('Failed to publish comment event')


@extend_schema(tags=['Stats'])
class StatsView(APIView):
    permission_classes = []

    @extend_schema(
        summary='Blog statistics and external data',
        description=(
            'Returns blog statistics combined with data from two external APIs fetched concurrently using asyncio.gather. '
            'Exchange rates from open.er-api.com and current Almaty time from timeapi.io. No authentication required.'
        ),
        responses={
            200: OpenApiResponse(description='Stats response'),
        },
        examples=[
            OpenApiExample(
                'Stats response',
                value={
                    'blog': {'total_posts': 42, 'total_comments': 137, 'total_users': 15},
                    'exchange_rates': {'KZT': 450.23, 'RUB': 89.10, 'EUR': 0.92},
                    'current_time': '2024-03-15T18:30:00+05:00',
                },
                response_only=True,
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        # Using async to fetch two external APIs concurrently; synchronous would double the latency
        data = asyncio.run(self._fetch_stats())
        return Response(data)

    async def _fetch_stats(self) -> dict:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Run both external API calls concurrently
        exchange_task = self._fetch_exchange_rates()
        time_task = self._fetch_current_time()
        exchange_data, time_data = await asyncio.gather(exchange_task, time_task)

        from asgiref.sync import sync_to_async
        blog_stats = await sync_to_async(self._get_blog_stats)()

        return {
            'blog': blog_stats,
            'exchange_rates': exchange_data,
            'current_time': time_data,
        }

    def _get_blog_stats(self) -> dict:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return {
            'total_posts': Post.objects.count(),
            'total_comments': Comment.objects.count(),
            'total_users': User.objects.count(),
        }

    async def _fetch_exchange_rates(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(EXTERNAL_API_EXCHANGE)
                data = response.json()
                rates = data.get('rates', {})
                return {
                    'KZT': rates.get('KZT'),
                    'RUB': rates.get('RUB'),
                    'EUR': rates.get('EUR'),
                }
        except Exception:
            logger.exception('Failed to fetch exchange rates')
            return {'KZT': None, 'RUB': None, 'EUR': None}

    async def _fetch_current_time(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(EXTERNAL_API_TIME)
                data = response.json()
                return data.get('dateTime', '')
        except Exception:
            logger.exception('Failed to fetch current time')
            return ''