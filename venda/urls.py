from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from rest_framework.response import Response
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.reverse import reverse

schema_view = get_schema_view(
   openapi.Info(
      title="API TRAINEE",
      default_version='v1',
      description="API de entrega para evitar desperdício de alimentos",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

class ApiRootView(APIView):
    """
    API Root — mostra endpoints diferentes para:
    - usuários não autenticados
    - lojas autenticadas
    - clientes autenticados
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        base = {
            "register": reverse("users-register", request=request),
            "login": reverse("users-login", request=request),
        }

        user = request.user
        if not user.is_authenticated:
            return Response(base)

        if getattr(user, "loja", False):
            base.update({
                "meu_cardapio": reverse("cardapios-list", request=request),
                "pedidos_em_andamento": reverse("pedidos-list", request=request),
            })
        else:
            base.update({
                "area_de_vendas": reverse("produtos-list", request=request),
                "buscar_por_loja": reverse("lojas-list", request=request),
                "metodos_de_pagamento": reverse("pagamentometodo-list", request=request),
                "historico_de_pedidos": reverse("pedidos-list", request=request),
            })

        return Response(base)


urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("admin/", admin.site.urls),

    # Apps principais
    path("api/users/", include("apps.users.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/pedidos/", include("apps.pedidos.urls")),

    # Documentação opcional
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
