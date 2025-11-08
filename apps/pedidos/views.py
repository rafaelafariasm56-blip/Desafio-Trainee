from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Pedido, Carrinho, CarrinhoItem, PedidoItem
from .serializers import PedidoSerializer, CarrinhoSerializer, CarrinhoItemSerializer
from django.db import transaction
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication

class CarrinhoViewSet(viewsets.ModelViewSet):
    serializer_class = CarrinhoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Carrinho.objects.filter(user=self.request.user)

    def get_object(self):
        carrinho, _ = Carrinho.objects.get_or_create(user=self.request.user)
        return carrinho

    def list(self, request, *args, **kwargs):
        carrinho = self.get_object()
        serializer = self.get_serializer(carrinho)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        carrinho = self.get_object()
        serializer = CarrinhoItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        produto = serializer.validated_data["produto"]
        quantidade = serializer.validated_data["quantidade"]

        item, criado = CarrinhoItem.objects.get_or_create(
            carrinho=carrinho,
            produto=produto,
            defaults={"quantidade": quantidade}
        )

        if not criado:
            item.quantidade += quantidade
            item.save()

        return Response(CarrinhoItemSerializer(item).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        carrinho = self.get_object()
        produto_id = request.data.get("produto_id")

        if not produto_id:
            return Response({"detail": "produto_id é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = carrinho.items.get(produto_id=produto_id)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CarrinhoItem.DoesNotExist:
            return Response({"detail": "Produto não encontrado no carrinho."}, status=status.HTTP_404_NOT_FOUND)
        

class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pedido.objects.filter(user=self.request.user).order_by("-criado_em")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user = request.user
        metodo_pagamento_id = request.data.get("metodo_pagamento")

        carrinho = Carrinho.objects.filter(user=user).first()
        if not carrinho or not carrinho.items.exists():
            return Response({"detail": "Carrinho vazio."}, status=status.HTTP_400_BAD_REQUEST)

        loja = carrinho.items.first().produto.loja
        pedido = Pedido.objects.create(
            user=user,
            loja=loja,
            metodo_pagamento_id=metodo_pagamento_id,
            total=carrinho.total
        )

        for item in carrinho.items.all():
            PedidoItem.objects.create(
                pedido=pedido,
                produto=item.produto,
                preco=item.produto.preco,
                quantidade=item.quantidade
            )

        carrinho.items.all().delete() 

        return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED)

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
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        loja = getattr(self.request.user, "loja", None)
        if not loja:
            return Pedido.objects.none()
        return Pedido.objects.filter(loja=loja).order_by("-criado_em")

    
class MeusPedidosViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return Pedido.objects.filter(user=self.request.user).order_by("-criado_em")
    def update(self, request, *args, **kwargs):
        pedido = self.get_object()
        novo_status = request.data.get("status")

        if novo_status not in dict(Pedido.STATUS_CHOICES):
            return Response({"erro": "Status inválido."}, status=status.HTTP_400_BAD_REQUEST)

        pedido.status = novo_status
        pedido.save()
        return Response(PedidoSerializer(pedido).data)