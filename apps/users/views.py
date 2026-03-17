from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .serializers import (
    RegisterSerializer,
    User,
    UserTimeSerializer,
    LanguageUpdateSerializer
)
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Update user language",
    description="Allows an authenticated user to change their preferred language.",
    tags=["Auth"],
)
@extend_schema(
    summary="Update user timezone",
    description="Allows an authenticated user to change their timezone.",
    tags=["Auth"],
)

class UpdateTimezoneView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserTimeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tz = serializer.validated_data["timezone"]

        request.user.timezone = tz
        request.user.save()

        return Response({
            "detail": _("Timezone updated successfully.")
        })


class UpdateLanguageView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = LanguageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.preferred_language = serializer.validated_data["language"]
        request.user.save()

        return Response({
            "detail": _("Language updated successfully.")
        })


class RegisterViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request):

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        context = {"user": user}

        subject = render_to_string(
            "emails/welcome/subject.txt",
            context
        ).strip()

        body = render_to_string(
            "emails/welcome/body.txt",
            context
        )

        send_mail(
            subject,
            body,
            "noreply@test.com",
            [user.email]
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)