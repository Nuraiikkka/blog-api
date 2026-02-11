import redis
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "listen to new comments via Redis pub/sub"
    def handle(self, *args, **options):
        r = redis.Redis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        pubsub.subscribe("comments")

        self.stdout.write("Listening to new comments...")

        for message in pubsub.listen():
            if message["type"] == "message":
                self.stdout.write(self.style.NOTICE(message["data"]))

