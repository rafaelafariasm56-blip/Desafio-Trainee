from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Pedido, Carrinho, CarrinhoItem, PedidoItem
from apps.users.permissions import IsDonoeReadOnly
from apps.users.models import Pagamento, Endereco
from apps.core.models import Produto
from .serializers import PedidoSerializer, CarrinhoSerializer, CarrinhoItemSerializer, CarrinhoAdicionarItemSerializer, MetodoPagamentoSerializer, PagamentoSerializer, AtualizarStatusPedidoSerializer, PedidoLojaSerializer, PagamentoSerializer, FinalizarPagamentoSerializer, FaturamentoFiltroSerializer, EnderecoSerializer, EnderecoCreateSerializer
from django.db import transaction
from rest_framework.decorators import action
from django.db.models import Sum, Count, Avg
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class CarrinhoViewSet(viewsets.ModelViewSet):
    """
    CRUD de carrinho.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Carrinho.objects.filter(user=self.request.user)

    def get_object(self):
        carrinho, _ = Carrinho.objects.get_or_create(user=self.request.user)
        return carrinho

    def get_serializer_class(self):
        if self.action == "create":
            return CarrinhoAdicionarItemSerializer
        return CarrinhoSerializer

    @swagger_auto_schema(
        operation_summary="Listar carrinho do usuário",
        operation_description="Retorna o carrinho atual do usuário autenticado com todos os itens.",
        responses={200: CarrinhoSerializer()}
    )
    def list(self, request, *args, **kwargs):
        carrinho = self.get_object()
        serializer = self.get_serializer(carrinho)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Adicionar item ao carrinho",
        operation_description=(
            "Adiciona um novo item ao carrinho. Caso o produto já exista no "
            "carrinho, a quantidade é somada."
        ),
    )
    def create(self, request, *args, **kwargs):
        carrinho = self.get_object()

        serializer = CarrinhoAdicionarItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        produto_id = serializer.validated_data["produto_id"]
        quantidade = serializer.validated_data["quantidade"]

        try:
            produto = Produto.objects.get(id=produto_id)
        except Produto.DoesNotExist:
            return Response({"detail": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if quantidade > produto.quantidade:
            return Response(
                {"detail": f"Estoque insuficiente. Disponível: {produto.quantidade}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item, criado = CarrinhoItem.objects.get_or_create(
            carrinho=carrinho,
            produto=produto,
            defaults={"quantidade": quantidade}
        )

        if not criado:
            if item.quantidade + quantidade > produto.quantidade:
                return Response(
                    {"detail": f"Quantidade total excede o estoque. Disponível: {produto.quantidade}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            item.quantidade += quantidade
            item.save()

        return Response(CarrinhoItemSerializer(item).data, status=status.HTTP_201_CREATED)


    @swagger_auto_schema(
        operation_summary="Remover item do carrinho",
        operation_description="Remove um item do carrinho pelo produto_id.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "produto_id": openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=["produto_id"]
        ),
    )
    def destroy(self, request, *args, **kwargs):
        carrinho = self.get_object()
        produto_id = request.data.get("produto_id")

        if not produto_id:
            return Response({"detail": "produto_id é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = carrinho.items.get(produto__id=produto_id)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except CarrinhoItem.DoesNotExist:
            return Response({"detail": "Produto não encontrado no carrinho."}, status=status.HTTP_404_NOT_FOUND)


        

class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Listar pedidos do usuário",
        responses={200: PedidoSerializer(many=True)}
    )
    def get_queryset(self):
        return Pedido.objects.filter(user=self.request.user).order_by("-criado_em")


    @swagger_auto_schema(
        operation_summary="Criar pedido a partir do carrinho",
        operation_description="Gera um pedido com base nos itens do carrinho do usuário.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "metodo_pagamento": openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=["metodo_pagamento"]
        ),
        responses={201: PedidoSerializer(), 400: "Carrinho vazio"}
    )
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
    serializer_class = PagamentoSerializer
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
            endereco=user.endereco,
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
            status__in=["entregue", "cancelado", "pendente", "a caminho", "preparando"]
        ).order_by("-criado_em")


class HistoricoLojaViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,viewsets.GenericViewSet):
    serializer_class = PedidoLojaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        loja = getattr(self.request.user, "lojaperfil", None)
        if not loja:
            return Pedido.objects.none()
        return Pedido.objects.filter(loja=loja).order_by("-criado_em")
    

class PedidoLojaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoLojaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        payload = self.request.auth or {}
        loja_id = payload.get("loja_id")

        if not loja_id:
            return Pedido.objects.none()  
        return Pedido.objects.filter(loja_id=loja_id).order_by("-criado_em")

    @action(detail=True, methods=["PATCH"], url_path="status")
    def atualizar_status(self, request, pk=None):
        payload = request.auth or {}
        loja_id = payload.get("loja_id")

        if not loja_id:
            return Response({"erro": "Acesso negado."}, status=403)

        try:
            pedido = Pedido.objects.get(pk=pk, loja_id=loja_id)
        except Pedido.DoesNotExist:
            return Response({"erro": "Pedido não encontrado."}, status=404)

        serializer = AtualizarStatusPedidoSerializer(pedido, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"mensagem": "Status atualizado com sucesso."})
    

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


class EnderecoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDonoeReadOnly]

    def get_queryset(self):
        return Endereco.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return EnderecoCreateSerializer
        return EnderecoSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PagamentoViewSet(viewsets.ModelViewSet):
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pagamento.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        pagamento = self.get_object()
        pagamento.ativo = False
        pagamento.save()
        return Response({"mensagem": "Método de pagamento removido."})

    @action(
        detail=False,
        methods=["GET"],
        url_path="listar",
        serializer_class=MetodoPagamentoSerializer
    )
    def listar_metodos(self, request):
        metodos = Pagamento.objects.filter(user=request.user, ativo=True)
        serializer = MetodoPagamentoSerializer(metodos, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["POST"],
        url_path="pagar",
        serializer_class=FinalizarPagamentoSerializer)
    
    def pagar(self, request):
        serializer = FinalizarPagamentoSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        pedidos = serializer.save()

        return Response(
            {
                "sucesso": True,
                "mensagem": "Pagamento concluído com sucesso.",
                "pedidos": [p.id for p in pedidos],
            },
            status=201,
        )



class FaturamentoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "periodo":
            return FaturamentoFiltroSerializer
        return None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            raise AttributeError("Defina get_serializer_class para esta action.")
        return serializer_class(*args, **kwargs)

    @action(detail=False, methods=["get", "post"])
    def periodo(self, request):

        dados = request.query_params if request.method == "GET" else request.data

        serializer = self.get_serializer(data=dados)
        serializer.is_valid(raise_exception=True)

        data_inicial = serializer.validated_data["data_inicial"]
        data_final = serializer.validated_data["data_final"]

        user = request.user

        pedidos = Pedido.objects.filter(
            loja=user.loja,
            status="entregue",             
            criado_em__date__range=[data_inicial, data_final]
        )

        resumo = pedidos.aggregate(
            total_faturado=Sum("total"),
            total_pedidos=Count("id"),
            ticket_medio=Avg("total")
        )

        return Response({
            "periodo": {
                "data_inicial": data_inicial,
                "data_final": data_final
            },
            "resumo": {
                "total_faturado": resumo["total_faturado"] or 0,
                "total_pedidos": resumo["total_pedidos"],
                "ticket_medio": resumo["ticket_medio"] or 0
            }
        })
