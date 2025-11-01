from rest_framework import routers
from django.urls import path, include
from apps.core.views import ProdutoViewSet

router = routers.DefaultRouter()
router.register(r"produtos", ProdutoViewSet, basename="produto")

urlpatterns = [
    path("", include(router.urls)),
]
