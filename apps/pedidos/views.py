from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Pedido, Carrinho, CarrinhoItem
from .serializers import PedidoSerializer, CarrinhoSerializer, CarrinhoItemSerializer, FinalizarCompraSerializer
from apps.users.permissions import IsClient, IsLoja
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

class CarrinhoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_carrinho(self, request):
        carrinho, created = Carrinho.objects.get_or_create(user=request.user)
        return carrinho

    def list(self, request):
        carrinho = self.get_carrinho(request)
        serializer = CarrinhoSerializer(carrinho)
        return Response(serializer.data)

    def create(self, request):
        """Adiciona item ao carrinho"""
        carrinho = self.get_carrinho(request)
        serializer = CarrinhoItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        produto = serializer.validated_data["produto"]
        quantidade = serializer.validated_data.get("quantidade", 1)
        data = serializer.validated_data.get("data")

        item, created = CarrinhoItem.objects.get_or_create(
            carrinho=carrinho,
            produto=produto,
            data=data,
            defaults={"quantidade": quantidade},
        )

        if not created:
            item.quantidade += quantidade
            item.save()

        return Response(CarrinhoSerializer(carrinho).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """Remove item do carrinho"""
        carrinho = self.get_carrinho(request)
        try:
            item = carrinho.items.get(pk=pk)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CarrinhoItem.DoesNotExist:
            return Response({"detail": "Item não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    def clear(self, request):
        """Limpa todo o carrinho"""
        carrinho = self.get_carrinho(request)
        carrinho.items.all().delete()
        return Response({"detail": "Carrinho esvaziado com sucesso."})
    

    @action(detail=False, methods=["post"], url_path="remover")
    def remover_item(self, request):
        produto_id = request.data.get("produto")
        carrinho = Carrinho.objects.get(user=request.user)
        carrinho.items.filter(produto_id=produto_id).delete()
        return Response(CarrinhoSerializer(carrinho).data)

    @action(detail=False, methods=["post"], url_path="finalizar")
    def finalizar_compra(self, request):
        serializer = FinalizarCompraSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        return Response({"message": f"Pedido {pedido.code} criado com sucesso!"}, status=status.HTTP_201_CREATED)

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.loja and hasattr(user, 'lojaperfil'):
            return Pedido.objects.filter(loja=user.lojaperfil)
        return Pedido.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        if user.loja:
            raise PermissionDenied("Lojas não podem criar pedidos.")
        serializer.save(user=user)

    @action(detail=True, methods=["patch"], permission_classes=[permissions.IsAuthenticated])
    def atualizar_status(self, request, pk=None):
        pedido = self.get_object()
        user = request.user

        if not user.loja or not hasattr(user, "lojaperfil"):
            raise PermissionDenied("Apenas lojas podem alterar o status de pedidos.")

        if pedido.loja != user.lojaperfil:
            raise PermissionDenied("Este pedido não pertence à sua loja.")

        novo_status = request.data.get("status")
        if novo_status not in dict(Pedido.STATUS_CHOICES):
            return Response({"detail": "Status inválido."}, status=status.HTTP_400_BAD_REQUEST)

        pedido.status = novo_status
        pedido.save()
        return Response({"detail": f"Status atualizado para '{novo_status}'."})

class HistoricoPedidoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Pedido.objects.filter(
            user=user,
            status__in=["entregue", "cancelado"]
        ).order_by("-criado_em")

class HistoricoLojaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated, IsLoja]

    def get_queryset(self):
        user = self.request.user

        if not hasattr(user, "lojaperfil"):
            raise PermissionDenied("Somente lojas com perfil podem acessar seus pedidos.")

        return Pedido.objects.filter(
            loja=user.lojaperfil,
            status__in=["pendente", "preparando", "a caminho"]
        ).order_by("criado_em")