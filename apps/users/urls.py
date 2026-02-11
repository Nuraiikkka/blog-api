from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterViewSet

router = DefaultRouter()
router.register("register", RegisterViewSet, basename="register")

urlpatterns = [
    *router.urls,
    path("token/", TokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
]