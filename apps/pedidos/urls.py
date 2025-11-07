from rest_framework.routers import DefaultRouter
from .views import PedidoViewSet, HistoricoPedidoViewSet, HistoricoLojaViewSet, CarrinhoViewSet

router = DefaultRouter()
router.register(r'pedidos', PedidoViewSet, basename='pedidos')
router.register(r'historico', HistoricoPedidoViewSet, basename='historico-pedidos')
router.register(r'historico-loja', HistoricoLojaViewSet, basename='historico-loja')
router.register(r"carrinho", CarrinhoViewSet, basename="carrinho")

urlpatterns = router.urls