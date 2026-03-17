from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import CategoryViewSet, TagViewSet, PostViewSet, CommentViewSet
from .views_stats import StatsView

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("tags", TagViewSet, basename="tag")
router.register("posts", PostViewSet, basename="post")
router.register("comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("stats/", StatsView.as_view(), name="stats"),
]

urlpatterns += router.urls