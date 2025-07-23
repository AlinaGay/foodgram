"""
Custom permissions for Foodgram API.

Defines object-level permissions for author access and safe methods.
"""

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Allows access only to the author or for safe methods."""

    def has_object_permission(self, request, view, obj):
        """
        Return True if request is safe or user is the author/admin.

        Safe methods are read-only (GET, HEAD, OPTIONS).
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated
            and (obj.author == request.user or request.user.is_admin)
        )
