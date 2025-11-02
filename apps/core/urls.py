from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import ProdutoViewSet, LojaViewSet, CardapioViewSet

router = DefaultRouter()
router.register(r'produtos', ProdutoViewSet, basename='produto')
router.register(r'lojas', LojaViewSet, basename='loja')
router.register(r'cardapios', CardapioViewSet, basename='cardapio')

urlpatterns = [
    path('', include(router.urls)),
]