from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source='comment.id', read_only=True)
    post_slug = serializers.CharField(source='comment.post.slug', read_only=True)
    author_email = serializers.CharField(source='comment.author.email', read_only=True)
    body = serializers.CharField(source='comment.body', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'comment_id', 'post_slug', 'author_email', 'body', 'is_read', 'created_at']
