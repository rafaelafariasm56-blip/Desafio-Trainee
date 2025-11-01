from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsLoja(BasePermission):
    #only lojas
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.loja)

class IsClient(BasePermission):
    #only clientes
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.loja)

class IsDonoeReadOnly(BasePermission):
    #SoODonoEscreveOrestoLe
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return hasattr(obj, "user") and obj.user == request.user
