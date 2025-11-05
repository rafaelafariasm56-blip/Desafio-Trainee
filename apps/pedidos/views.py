from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Pedido, Carrinho
from .serializers import PedidoSerializer, CarrinhoSerializer, PedidoHistoricoSerializer
from apps.users.permissions import IsClient
from apps.core.models import LojaPerfil


class CarrinhoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsClient]

    def list(self, request):
        carrinho, _ = Carrinho.objects.get_or_create(user=request.user)
        serializer = CarrinhoSerializer(carrinho)
        return Response(serializer.data)


class PedidoViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = PedidoHistoricoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pedido.objects.filter(user=self.request.user).order_by('-criado_em')