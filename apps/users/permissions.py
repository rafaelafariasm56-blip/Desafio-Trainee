from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsLoja(BasePermission):
    """
    Permite acesso apenas a quem possui claim is_loja = True
    """
    def has_permission(self, request, view):
        claims = request.auth or {}
        return bool(claims.get("is_loja"))


class IsClient(BasePermission):
    """
    Permite acesso apenas a usuários comuns (não-loja)
    """
    def has_permission(self, request, view):
        claims = request.auth or {}
        return bool(claims.get("is_loja") is False)


class IsDonoeReadOnly(BasePermission):
    """
    Permite edição apenas pelo dono do objeto.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        claims = request.auth or {}
        user_id = claims.get("user_id")

        return hasattr(obj, "user_id") and obj.user_id == user_id