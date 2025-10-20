from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Pedido
from .serializers import PedidoSerializer
from users.permissions import EhCliente, EhLoja

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().select_related("cliente", "loja").order_by("-criado_em")
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "CLIENTE":
            return Pedido.objects.filter(cliente=user).order_by("-criado_em")
        elif user.role == "LOJA":
            return Pedido.objects.filter(loja=user).order_by("criado_em")
        return Pedido.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != "CLIENTE":
            raise permissions.PermissionDenied("Apenas clientes podem criar pedidos.")
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[EhLoja])
    def atualizar_status(self, request, pk=None):
        pedido = self.get_object()
        novo_status = request.data.get("status")
        if novo_status not in dict(pedido.STATUS):
            return Response({"erro": "Status inválido"}, status=400)
        pedido.status = novo_status
        pedido.save()
        return Response({"status": pedido.status})

    @action(detail=True, methods=["post"], permission_classes=[EhCliente])
    def cancelar(self, request, pk=None):
        pedido = self.get_object()
        if pedido.status in ["ENTREGUE", "CANCELADO"]:
            return Response({"erro": "Pedido não pode ser cancelado."}, status=400)
        pedido.status = "CANCELADO"
        pedido.save()
        for item in pedido.itens.all():
            oferta = item.oferta
            oferta.quantidade_disponivel += item.quantidade
            oferta.save()
        return Response({"status": "Pedido cancelado com sucesso."})
