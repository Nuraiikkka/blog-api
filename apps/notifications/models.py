import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.blog.models import Comment

logger = logging.getLogger('apps.notifications')

User = get_user_model()


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name=_('recipient'))
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='notifications', verbose_name=_('comment'))
    is_read = models.BooleanField(_('is read'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Notification for {self.recipient} on comment {self.comment_id}'
