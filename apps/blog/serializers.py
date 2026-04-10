import logging

import pytz
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers

from apps.blog.models import Category, Comment, Post, Tag
from apps.users.serializers import UserSerializer

logger = logging.getLogger('apps.blog')


class CategorySerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Category)

    class Meta:
        model = Category
        fields = ['id', 'slug', 'translations']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'body', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', many=True, write_only=True, required=False
    )
    created_at_localized = serializers.SerializerMethodField()
    updated_at_localized = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'title', 'slug', 'body', 'category', 'category_id',
            'tags', 'tag_ids', 'status', 'created_at', 'updated_at',
            'created_at_localized', 'updated_at_localized',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'slug']

    def get_created_at_localized(self, obj: Post) -> str:
        return self._localize_datetime(obj.created_at)

    def get_updated_at_localized(self, obj: Post) -> str:
        return self._localize_datetime(obj.updated_at)

    def _localize_datetime(self, dt) -> str:
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_tz = request.user.timezone or 'UTC'
            try:
                tz = pytz.timezone(user_tz)
                dt = dt.astimezone(tz)
            except Exception:
                pass
        return date_format(dt, use_l10n=True)

    def create(self, validated_data: dict) -> Post:
        tags = validated_data.pop('tags', [])
        request = self.context.get('request')
        validated_data['author'] = request.user
        if not validated_data.get('slug'):
            from django.utils.text import slugify
            validated_data['slug'] = slugify(validated_data['title'])
        post = Post.objects.create(**validated_data)
        post.tags.set(tags)
        logger.info('Post created: %s by %s', post.slug, request.user.email)
        return post

    def update(self, instance: Post, validated_data: dict) -> Post:
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        logger.info('Post updated: %s', instance.slug)
        return instance
