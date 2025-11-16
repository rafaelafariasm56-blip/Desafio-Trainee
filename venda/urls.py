from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from apps.users.views import ApiRootView, PainelUsuarioView, PainelLojaView

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="API TRAINEE",
        default_version="v1",
        description="API de entrega para evitar desperdício de alimentos",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),

    path("admin/", admin.site.urls),

    path("api-auth/", include("rest_framework.urls")),

    path("api/users/", include(("apps.users.urls", "users"), namespace="users")),

    path("api/core/", include("apps.core.urls")),

    path("api/pedidos/", include(("apps.pedidos.urls", "pedidos"), namespace="pedidos")),

    path("painel/usuario/", PainelUsuarioView.as_view(), name="painel-usuario"),
    path("painel/loja/", PainelLojaView.as_view(), name="painel-loja"),

    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
