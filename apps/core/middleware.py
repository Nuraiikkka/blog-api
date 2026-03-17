from django.utils import translation


class LanguageMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        lang = None

        if request.user.is_authenticated:
            lang = request.user.preferred_language

        if not lang:
            lang = request.GET.get("lang")

        if not lang:
            lang = request.headers.get("Accept-Language")

            if lang:
                lang = lang.split(",")[0][:2]

        if lang not in ["en", "ru", "kk"]:
            lang = "en"

        translation.activate(lang)

        request.LANGUAGE_CODE = lang

        response = self.get_response(request)

        return response