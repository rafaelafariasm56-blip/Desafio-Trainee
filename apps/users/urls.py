from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from apps.core.views import ProdutoViewSet, PagamentoListCreateView, PagamentoDetailView
from apps.users.views import PainelUsuarioView, PainelLojaView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny
from apps.users.views_auth import CustomLoginView
from django.shortcuts import redirect


class ApiRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if getattr(request.user, "loja", False):
                return redirect("painel-loja")
            return redirect("painel-usuario")

        return Response({
            "register": reverse("users-register", request=request),
            "login": request.build_absolute_uri("/api-auth/login/?next=/api/users/"),
        })

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("produtos", ProdutoViewSet, basename="produtos")

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),

    path("painel/usuario/", PainelUsuarioView.as_view(), name="painel-usuario"),
    path("painel/loja/", PainelLojaView.as_view(), name="painel-loja"),
    path("pagamentos/", PagamentoListCreateView.as_view(), name="pagamentos-list"),
    path("pagamentos/<int:pk>/", PagamentoDetailView.as_view(), name="pagamentos-detail"),
    path("users/register/", UserViewSet.as_view({"post": "register"}), name="users-register"),
    path("users/login/", UserViewSet.as_view({"post": "login"}), name="users-login"),
    path("", include(router.urls)),
    path("api-auth/login/", CustomLoginView.as_view(), name="login"),
]