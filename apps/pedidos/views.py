from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Pedido, Carrinho, CarrinhoItem, PedidoItem
from apps.core.models import Produto
from apps.users.models import Pagamento
from .serializers import PedidoSerializer, CarrinhoSerializer, CarrinhoItemSerializer, MetodoPagamentoSerializer, PagamentoSerializer, AtualizarStatusPedidoSerializer, PedidoLojaSerializer, PagamentoSerializer, FinalizarPagamentoSerializer
from django.db import transaction
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.decorators import action
from rest_framework.views import APIView


def get_carrinho(usuario):
    carrinho, _ = Carrinho.objects.get_or_create(usuario=usuario)
    return carrinho


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


class MetodoPagamentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pagamento.objects.all()
    serializer_class = MetodoPagamentoSerializer
    permission_classes = [permissions.AllowAny]
        

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
        total = carrinho.total

        pedido = Pedido.objects.create(
            user=user,
            loja=loja,
            metodo_pagamento_id=metodo_pagamento_id,
            total=total,
        )

        for item in carrinho.items.all():
            PedidoItem.objects.create(
                pedido=pedido,
                produto=item.produto,
                preco=item.produto.preco,
                quantidade=item.quantidade,
                data=item.data,
            )

        carrinho.items.all().delete()

        return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED)



class HistoricoPedidoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pedido.objects.filter(
            user=self.request.user,
            status__in=["entregue", "cancelado"]
        ).order_by("-criado_em")



class HistoricoLojaViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,viewsets.GenericViewSet):
    serializer_class = PedidoLojaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        loja = getattr(self.request.user, "lojaperfil", None)
        if not loja:
            return Pedido.objects.none()
        return Pedido.objects.filter(loja=loja).order_by("-criado_em")
    

class PedidoLojaViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = AtualizarStatusPedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pedido.objects.filter(loja__user=self.request.user)

    @action(detail=True, methods=['patch'])
    def atualizar_status(self, request, pk=None):
        pedido = self.get_object()
        serializer = self.get_serializer(pedido, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

class MeusPedidosViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

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

class PagamentoViewSet(viewsets.ModelViewSet):
    queryset = Pagamento.objects.all()
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pagamento.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "pagar":
            if self.request.method == "POST":
                return FinalizarPagamentoSerializer
            else:
                return MetodoPagamentoSerializer  
        return PagamentoSerializer

    @action(detail=False, methods=["get", "post"], url_path="pagar")
    def pagar(self, request):
        user = request.user

        if request.method == "GET":
            metodos = Pagamento.objects.filter(user=user, ativo=True)
            serializer = MetodoPagamentoSerializer(metodos, many=True)
            return Response(serializer.data)

        serializer = FinalizarPagamentoSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        pedidos = serializer.save()

        return Response(
            {
                "sucesso": "Pagamento realizado!",
                "pedidos": [p.id for p in pedidos],
            },
            status=201
        )

