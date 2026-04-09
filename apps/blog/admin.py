from django.contrib import admin
from parler.admin import TranslatableAdmin

from apps.blog.models import Category, Comment, Post, Tag


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['slug']
    prepopulated_fields = {}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at']
    raw_id_fields = ['author', 'post']