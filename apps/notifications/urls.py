from django.urls import path

from apps.notifications.views import (
    NotificationCountView,
    NotificationListView,
    NotificationMarkReadView,
    post_stream,
)

urlpatterns = [
    path('posts/stream/', post_stream, name='post-stream'),
    path('notifications/count/', NotificationCountView.as_view(), name='notification-count'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/read/', NotificationMarkReadView.as_view(), name='notification-read'),
]
