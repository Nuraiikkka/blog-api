from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Category, Tag, Post, Comment
from django.utils import translation

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Comment
        fields = ("id", "post", "author", "body", "created_at")

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ("author",)

from django.utils import translation

class CategorySerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name"]

    def get_name(self, obj):
        lang = translation.get_language()

        if lang == "ru":
            return obj.name_ru

        if lang == "kz":
            return obj.name_kk

        return obj.name_en