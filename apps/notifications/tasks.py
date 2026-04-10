import json
import logging

from celery import shared_task

logger = logging.getLogger('apps.notifications')


# Retries matter for comment side effects: creating the Notification record and
# pushing the WebSocket message are critical for user experience. A transient DB
# or Redis failure should not permanently drop the notification — retrying with
# backoff ensures eventual delivery without blocking the HTTP response.
@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_new_comment(comment_id: int) -> None:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from apps.blog.models import Comment
    from apps.notifications.models import Notification

    try:
        comment = Comment.objects.select_related('author', 'post__author').get(id=comment_id)
    except Comment.DoesNotExist:
        logger.warning('process_new_comment: comment %s not found', comment_id)
        return

    post = comment.post
    post_author = post.author

    if post_author != comment.author:
        Notification.objects.get_or_create(recipient=post_author, comment=comment)
        logger.info('Notification created for user %s', post_author.email)

    channel_layer = get_channel_layer()
    group_name = f'post_{post.slug}_comments'
    message = {
        'comment_id': comment.id,
        'author': {'id': comment.author.id, 'email': comment.author.email},
        'body': comment.body,
        'created_at': comment.created_at.isoformat(),
    }
    async_to_sync(channel_layer.group_send)(group_name, {
        'type': 'new_comment',
        'message': message,
    })
    logger.info('WebSocket message sent to group %s', group_name)
