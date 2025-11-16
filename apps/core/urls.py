from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import LojaViewSet, ProdutoViewSet, CardapioViewSet

router = DefaultRouter()
router.register("lojas", LojaViewSet, basename="lojas")
router.register("produtos", ProdutoViewSet, basename="produtos")
router.register("cardapio", CardapioViewSet, basename="cardapio")

urlpatterns = [
    path("", include(router.urls)),
]
