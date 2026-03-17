from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from zoneinfo import available_timezones
from django.core.mail import send_mail
from django.template.loader import render_to_string

User = get_user_model()


class UserTimeSerializer(serializers.Serializer):
    timezone = serializers.CharField()
    def validate_timezone(self, value: str) -> str:
        if value not in available_timezones:
            raise serializers.ValidationError(
                _("Invalid timezone. Must be valid IANA timezone.")
            )
        return value

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)

        refresh = RefreshToken.for_user(user)

        return {
            "user": user,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class LanguageUpdateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=settings.LANGUAGES,
        error_messages={
            "invalid_choice": _("Unsupported language.")
        }
    )


class TimezoneUpdateSerializer(serializers.Serializer):
    timezone = serializers.CharField()

    def validate_timezone(self, value):
        if value not in available_timezones():
            raise serializers.ValidationError(
                _("Invalid timezone.")
            )
        return value

class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password"]

    def create(self, validated_data):

        user = User.objects.create_user(**validated_data)

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

        return user
