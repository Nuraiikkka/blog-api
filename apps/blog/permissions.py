from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
