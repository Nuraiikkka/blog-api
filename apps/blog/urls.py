from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.blog.views import PostViewSet, StatsView

router = DefaultRouter()
router.register('posts', PostViewSet, basename='posts')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', StatsView.as_view(), name='stats'),
]
