from rest_framework import viewsets, permissions
from django.core.cache import cache
from rest_framework.response import Response
import json
import redis
from django.conf import settings

from .models import Category, Tag, Post, Comment
from .serializers import (
    CategorySerializer,
    TagSerializer,
    PostSerializer,
    CommentSerializer,
)
from .permissions import IsOwnerOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return Post.objects.filter(status="published")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        cache.delete("posts_list")

    def list(self, request, *args, **kwargs):
        cached = cache.get("posts_list")
        if cached:
            return Response(cached)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        cache.set("posts_list", serializer.data, timeout=60)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)

        r = redis.Redis.from_url(settings.REDIS_URL)
        r.publish(
            "comments",
            json.dumps(
                {
                    "post": comment.post.id,
                    "author": str(comment.author),
                    "body": comment.body,
                }
            ),
        )