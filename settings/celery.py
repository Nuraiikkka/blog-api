import os

from celery import Celery
from celery.schedules import crontab

ENV_ID = os.environ.get('BLOG_ENV_ID', 'local')
if ENV_ID == 'prod':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.local')

app = Celery('blogapi')

# Pull configuration from Django settings (CELERY_* namespace).
# broker_url and result_backend are set there via CELERY_BROKER_URL.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(['apps.users', 'apps.blog', 'apps.notifications'])

app.conf.beat_schedule = {
    'publish-scheduled-posts-every-minute': {
        'task': 'apps.blog.tasks.publish_scheduled_posts',
        'schedule': 60.0,
    },
    'clear-expired-notifications-daily': {
        'task': 'apps.blog.tasks.clear_expired_notifications',
        'schedule': crontab(hour=3, minute=0),
    },
    'generate-daily-stats': {
        'task': 'apps.blog.tasks.generate_daily_stats',
        'schedule': crontab(hour=0, minute=0),
    },
}

app.conf.timezone = 'UTC'
