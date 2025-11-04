from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Pedido
from .serializers import PedidoSerializer
from apps.users.permissions import IsClient
from apps.core.models import LojaPerfil
from apps.pedidos.serializers import CarrinhoSerializer
from apps.pedidos.models import Carrinho
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


class CarrinhoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsClient]

    def list(self, request):
        carrinho, _ = Carrinho.objects.get_or_create(user=request.user)
        serializer = CarrinhoSerializer(Carrinho)
        return Response(serializer.data)


class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.loja:
            return Pedido.objects.filter(cliente=user)

        return Pedido.objects.filter(loja__user=user)

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user)

    def perform_destroy(self, instance):
        if instance.cliente != self.request.user:
            raise PermissionDenied("Você não pode cancelar este pedido.")
        instance.delete()