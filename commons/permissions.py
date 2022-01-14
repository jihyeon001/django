from django.contrib.auth        import get_user_model
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrMemberReadOnly(BasePermission):
    def has_queryset_permission(self, request, view, queryset):
        obj = queryset.first()
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return True
            elif hasattr(obj, 'user'):
                return obj.user.id == request.user.id
            elif obj.__class__ == get_user_model():
                return obj.id == request.user.id
            elif hasattr(obj, 'Member'):
                if obj.member.id == request.user.member.id:
                    return request.method in SAFE_METHODS
            elif obj.__class__.__name__ == 'Member':
                if obj.id == request.user.member.id:
                    return request.method in SAFE_METHODS
            return False
        else:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return True
            elif hasattr(obj, 'user'):
                return obj.user.id == request.user.id
            elif obj.__class__ == get_user_model():
                return obj.id == request.user.id
            elif hasattr(obj, 'Member'):
                if obj.member.id == request.user.member.id:
                    return request.method in SAFE_METHODS
            elif obj.__class__.__name__ == 'Member':
                if obj.id == request.user.member.id:
                    return request.method in SAFE_METHODS
            return False
        else:
            return False