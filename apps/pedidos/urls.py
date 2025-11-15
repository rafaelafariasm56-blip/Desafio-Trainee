from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HistoricoPedidoViewSet, HistoricoLojaViewSet, MeusPedidosViewSet, CarrinhoViewSet, PagamentoViewSet, FaturamentoViewSet

app_name = "pedidos"

router = DefaultRouter()
router.register("carrinho", CarrinhoViewSet, basename="carrinho")
router.register("historico-pedidos", HistoricoPedidoViewSet, basename="historico-pedidos")
router.register("historico-loja", HistoricoLojaViewSet, basename="historico-loja")
router.register("meus-pedidos", MeusPedidosViewSet, basename="meus-pedidos")
router.register("pagamento", PagamentoViewSet, basename="pagamento")  
router.register("faturamento", FaturamentoViewSet, basename="faturamento")

urlpatterns = [
    path("", include(router.urls)),  
]