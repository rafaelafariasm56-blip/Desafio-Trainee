"""
URL configuration for venda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from rest_framework.response import Response
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView


schema_view = get_schema_view(
   openapi.Info(
      title="API TRAINEE",
      default_version='v1',
      description="API de entrega para evitar desperdício de alimentos",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
class APIRootView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "message": "API",
            "version": "v1",
            "docs": {
                "swagger": request.build_absolute_uri("/swagger/"),
                "redoc": request.build_absolute_uri("/redoc/"),
            },
            "apps": {
                "users": request.build_absolute_uri("/api/users/"),
                "core": request.build_absolute_uri("/api/core/"),
                "pedidos": request.build_absolute_uri("/api/pedidos/"),
            },
            "auth": {
                "token_obtain": request.build_absolute_uri("/api/auth/token/"),
                "token_refresh": request.build_absolute_uri("/api/auth/token/refresh/"),
            },
        })
    
urlpatterns = [
    path("", APIRootView.as_view(), name="api-root"),
    path("admin/", admin.site.urls),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/users/", include("apps.users.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/pedidos/", include("apps.pedidos.urls")),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]