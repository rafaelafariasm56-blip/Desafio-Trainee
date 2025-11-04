from rest_framework.routers import DefaultRouter
from apps.core.views import LojaViewSet, ProdutoViewSet, CardapioViewSet

router = DefaultRouter()
router.register(r'lojas', LojaViewSet, basename='lojas')
router.register(r'produtos', ProdutoViewSet, basename='produtos')
router.register(r'cardapios', CardapioViewSet, basename='cardapios')

urlpatterns = router.urls