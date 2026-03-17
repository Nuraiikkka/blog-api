import asyncio
import httpx

from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Post, Comment
from apps.users.models import User


class StatsView(APIView):
    async def get(self, request):

        async with httpx.AsyncClient() as client:

            rates_request = client.get(
                "https://open.er-api.com/v6/latest/USD"
            )

            time_request = client.get(
                "https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty"
            )

            rates_response, time_response = await asyncio.gather(
                rates_request,
                time_request
            )

        rates_json = rates_response.json()
        time_json = time_response.json()

        return Response({
            "blog": {
                "total_posts": Post.objects.count(),
                "total_comments": Comment.objects.count(),
                "total_users": User.objects.count()
            },
            "exchange_rates": {
                "KZT": rates_json["rates"]["KZT"],
                "RUB": rates_json["rates"]["RUB"],
                "EUR": rates_json["rates"]["EUR"]
            },
            "current_time": time_json["dateTime"]
        })