from __future__ import annotations
from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name

class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title= models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    body = models.TextField()

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null = True, blank = True)
    tags = models.ManyToManyField(Tag, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Comment(models.Model):
    post=models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(Post, on_delete=models.CASCADE)
    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self)->str:
        return f"Comment by{self.author}"

class Category(models.Model):

    name_en = models.CharField(max_length=100)

    name_ru = models.CharField(max_length=100)

    name_kz = models.CharField(max_length=100)

    def __str__(self):
        return self.name_en

