import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger('apps.users')

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar', 'preferred_language', 'timezone', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm', 'preferred_language']

    def validate(self, attrs: dict) -> dict:
        if attrs['password'] != attrs.pop('password_confirm'):
            logger.warning('Registration failed: passwords do not match for email %s', attrs.get('email'))
            raise serializers.ValidationError({'password_confirm': _('Passwords do not match.')})
        return attrs

    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            preferred_language=validated_data.get('preferred_language', 'en'),
        )
        return user


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class RegisterResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = TokenPairSerializer()


class LanguageSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=['en', 'ru', 'kk'])


class TimezoneSerializer(serializers.Serializer):
    timezone = serializers.CharField(max_length=100)

    def validate_timezone(self, value: str) -> str:
        import pytz
        if value not in pytz.all_timezones:
            raise serializers.ValidationError(_('Invalid timezone. Use a valid IANA timezone identifier.'))
        return value