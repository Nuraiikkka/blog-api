from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import render
from .serializers import RegisterSerializer, User


class RegisterViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        return Response(data, status=status.HTTP_201_CREATED)

