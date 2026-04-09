import logging

import pytz
from django.utils import timezone, translation

from apps.users.constants import LANGUAGE_EN, SUPPORTED_LANGUAGES

logger = logging.getLogger('apps.core')


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = self._resolve_language(request)
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        if hasattr(request, 'user') and request.user.is_authenticated:
            user_tz = request.user.timezone or 'UTC'
            try:
                tz = pytz.timezone(user_tz)
                timezone.activate(tz)
            except Exception:
                timezone.activate(pytz.UTC)
        else:
            timezone.activate(pytz.UTC)

        response = self.get_response(request)
        translation.deactivate()
        timezone.deactivate()
        return response

    def _resolve_language(self, request) -> str:
        if hasattr(request, 'user') and request.user.is_authenticated:
            lang = getattr(request.user, 'preferred_language', None)
            if lang and lang in SUPPORTED_LANGUAGES:
                return lang

        lang = request.GET.get('lang')
        if lang and lang in SUPPORTED_LANGUAGES:
            return lang

        accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for candidate in accept_lang.split(','):
            code = candidate.split(';')[0].strip().split('-')[0].lower()
            if code in SUPPORTED_LANGUAGES:
                return code

        return LANGUAGE_EN