import logging

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import (
    LanguageSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    TimezoneSerializer,
    UserSerializer,
)

logger = logging.getLogger('apps.users')

User = get_user_model()


@extend_schema(tags=['Auth'])
class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    throttle_classes = []

    def get_throttles(self):
        if self.action == 'create':
            from apps.blog.throttles import RegisterRateThrottle
            return [RegisterRateThrottle()]
        return super().get_throttles()

    @extend_schema(
        summary='Register a new user',
        description=(
            'Creates a new user account. Returns user data and JWT token pair. '
            'Sends a welcome email in the user\'s preferred language. '
            'Rate limited to 5 requests per minute per IP.'
        ),
        request=RegisterSerializer,
        responses={
            201: RegisterResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            429: OpenApiResponse(description='Too many requests'),
        },
        examples=[
            OpenApiExample(
                'Register request',
                value={
                    'email': 'user@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'password': 'securepass123',
                    'password_confirm': 'securepass123',
                    'preferred_language': 'en',
                },
                request_only=True,
            ),
            OpenApiExample(
                'Register response',
                value={
                    'user': {
                        'id': 1,
                        'email': 'user@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                    },
                    'tokens': {
                        'access': 'eyJ...',
                        'refresh': 'eyJ...',
                    },
                },
                response_only=True,
            ),
        ],
    )
    def create(self, request: Request) -> Response:
        logger.info('Registration attempt for email: %s', request.data.get('email'))
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning('Registration failed for email: %s errors: %s', request.data.get('email'), serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        logger.info('User registered: %s', user.email)

        from apps.users.tasks import send_welcome_email
        send_welcome_email.delay(user.id)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
        }, status=status.HTTP_201_CREATED)

    def _send_welcome_email(self, user: User) -> None:
        lang = user.preferred_language or 'en'
        with translation.override(lang):
            subject = render_to_string('emails/welcome/subject.txt', {'user': user}).strip()
            body = render_to_string('emails/welcome/body.txt', {'user': user})
            try:
                send_mail(subject, body, None, [user.email])
                logger.info('Welcome email sent to: %s', user.email)
            except Exception:
                logger.exception('Failed to send welcome email to: %s', user.email)

    @extend_schema(
        summary='Update preferred language',
        description='Updates the authenticated user\'s preferred language. Supported: en, ru, kk.',
        request=LanguageSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Invalid language'),
            401: OpenApiResponse(description='Authentication required'),
        },
        tags=['Auth'],
    )
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated], url_path='language')
    def set_language(self, request: Request) -> Response:
        serializer = LanguageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        request.user.preferred_language = serializer.validated_data['language']
        request.user.save(update_fields=['preferred_language'])
        logger.info('User %s updated language to %s', request.user.email, request.user.preferred_language)
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        summary='Update timezone',
        description='Updates the authenticated user\'s timezone. Must be a valid IANA timezone identifier.',
        request=TimezoneSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Invalid timezone'),
            401: OpenApiResponse(description='Authentication required'),
        },
        tags=['Auth'],
    )
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated], url_path='timezone')
    def set_timezone(self, request: Request) -> Response:
        serializer = TimezoneSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        request.user.timezone = serializer.validated_data['timezone']
        request.user.save(update_fields=['timezone'])
        logger.info('User %s updated timezone to %s', request.user.email, request.user.timezone)
        return Response(UserSerializer(request.user).data)
