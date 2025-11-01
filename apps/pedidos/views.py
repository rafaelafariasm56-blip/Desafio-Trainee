from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Pedido
from .serializers import PedidoSerializer
from apps.users.permissions import IsClient
from apps.core.models import LojaPerfil
from apps.pedidos.serializers import CarrinhoSerializer
from apps.pedidos.models import Carrinho
from rest_framework.permissions import IsAuthenticated

class CarrinhoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsClient]

    def list(self, request):
        carrinho, _ = Carrinho.objects.get_or_create(user=request.user)
        serializer = CarrinhoSerializer(Carrinho)
        return Response(serializer.data)


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().select_related("loja", "user")
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.loja:
            est = LojaPerfil.objects.get(user=user)
            return Pedido.objects.filter(
                loja=est,
                status__in=["pendente", "preparando", "a caminho"]
            ).order_by("criado_em")
        return Pedido.objects.filter(user=user).order_by("criado_em")