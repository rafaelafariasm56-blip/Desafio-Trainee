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
        default_version="v1",
        description="API de entrega para evitar desperdício de alimentos",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

class ApiRootView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({
            "register": reverse("users-register", request=request),
            "login": request.build_absolute_uri("/api-auth/login/?next=/api/users/")
        })

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/pedidos/", include(("apps.pedidos.urls", "pedidos"), namespace="pedidos")),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
