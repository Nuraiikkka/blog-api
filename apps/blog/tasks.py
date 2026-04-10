import logging

from celery import shared_task

logger = logging.getLogger('apps.blog')


# Retries matter for cache invalidation: if Redis is briefly unavailable,
# stale cache can serve incorrect data until it expires. Retrying ensures
# the cache is cleaned as soon as Redis recovers.
@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def invalidate_posts_cache() -> None:
    from django.core.cache import cache
    from apps.users.constants import SUPPORTED_LANGUAGES
    CACHE_KEY_POSTS = 'posts_list'
    for lang in SUPPORTED_LANGUAGES:
        for page in range(1, 20):
            cache.delete(f'{CACHE_KEY_POSTS}_{lang}_page_{page}')
    logger.info('Posts list cache invalidated via Celery task')


# Retries matter for scheduled post publishing: a transient DB or Redis failure
# should not permanently skip a post that was meant to be published. Retrying
# ensures eventual consistency without manual intervention.
@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def publish_scheduled_posts() -> None:
    import json
    from django.utils import timezone
    import redis as redis_client
    from django.conf import settings
    from apps.blog.models import Post
    from apps.blog.constants import PostStatus

    now = timezone.now()
    posts = Post.objects.filter(status=PostStatus.SCHEDULED, publish_at__lte=now)
    r = redis_client.from_url(settings.REDIS_URL)
    for post in posts:
        post.status = PostStatus.PUBLISHED
        post.save(update_fields=['status'])
        event = json.dumps({
            'post_id': post.id,
            'title': post.title,
            'slug': post.slug,
            'author': {'id': post.author.id, 'email': post.author.email},
            'published_at': post.updated_at.isoformat(),
        })
        r.publish('post_published', event)
        logger.info('Scheduled post published: %s', post.slug)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def clear_expired_notifications() -> None:
    from django.utils import timezone
    from datetime import timedelta
    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info('Cleared %d expired notifications', deleted)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_daily_stats() -> None:
    from django.utils import timezone
    from datetime import timedelta
    from django.contrib.auth import get_user_model
    from apps.blog.models import Post, Comment

    User = get_user_model()
    since = timezone.now() - timedelta(hours=24)
    new_posts = Post.objects.filter(created_at__gte=since).count()
    new_comments = Comment.objects.filter(created_at__gte=since).count()
    new_users = User.objects.filter(date_joined__gte=since).count()
    logger.info('Daily stats — posts: %d, comments: %d, users: %d', new_posts, new_comments, new_users)
