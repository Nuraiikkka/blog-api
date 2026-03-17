from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import pytz

class ChangeLanguageView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request):

        lang = request.data.get("language")

        if lang not in ["en","ru","kz"]:
            return Response({"error":"invalid language"}, status=400)

        request.user.language = lang
        request.user.save()

        return Response({"message":"language updated"})


class ChangeTimezoneView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request):

        tz = request.data.get("timezone")

        if tz not in pytz.all_timezones:
            return Response({"error":"invalid timezone"}, status=400)

        request.user.timezone = tz
        request.user.save()

        return Response({"message":"timezone updated"})