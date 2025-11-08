from rest_framework.routers import DefaultRouter
from .views import PedidoViewSet, HistoricoPedidoViewSet, HistoricoLojaViewSet, CarrinhoViewSet, MeusPedidosViewSet

router = DefaultRouter()
router.register(r'pedidos', PedidoViewSet, basename='pedidos')
router.register(r'historico', HistoricoPedidoViewSet, basename='historico-pedidos')
router.register("historico-loja", HistoricoLojaViewSet, basename="historico-loja")
router.register(r"carrinho", CarrinhoViewSet, basename="carrinho")
router.register("meus_pedidos", MeusPedidosViewSet, basename="meus_pedidos")

urlpatterns = router.urls