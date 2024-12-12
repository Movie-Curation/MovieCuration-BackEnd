from rest_framework.permissions import BasePermission

class IsExpertUser(BasePermission):
    """
    권한: 전문가 사용자만 허용
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_expert)

class IsAdminUser(BasePermission):
    """
    권한: 관리자만 허용
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)

class IsRegularUser(BasePermission):
    """
    권한: 일반 사용자만 허용
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.is_expert and not request.user.is_admin)