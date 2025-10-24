from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.pedidos.views import PedidoViewSet

router = DefaultRouter()
router.register("", PedidoViewSet, basename="pedidos")

urlpatterns = [
    path("", include(router.urls)),
]
