import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

from apps.blog.constants import PostStatus

logger = logging.getLogger('apps.blog')

User = get_user_model()


class Category(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100)
    )
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self) -> str:
        return self.safe_translation_getter('name', any_language=True) or self.slug


class Tag(models.Model):
    name = models.CharField(_('name'), max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name=_('author'))
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(unique=True)
    body = models.TextField(_('body'))
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name=_('category'),
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name=_('tags'))
    publish_at = models.DateTimeField(_('publish at'), null=True, blank=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name=_('post'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name=_('author'))
    body = models.TextField(_('body'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'Comment by {self.author} on {self.post}'
