from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Pedido, Carrinho, CarrinhoItem, PedidoItem
from apps.users.permissions import IsDonoeReadOnly
from apps.users.models import Pagamento, Endereco
from apps.core.models import Produto
from .serializers import PedidoSerializer, CarrinhoSerializer, CarrinhoItemSerializer, CarrinhoAdicionarItemSerializer, MetodoPagamentoSerializer, PagamentoSerializer, AtualizarStatusPedidoSerializer, PedidoLojaSerializer, PagamentoSerializer, FinalizarPagamentoSerializer, FaturamentoFiltroSerializer, EnderecoSerializer, EnderecoCreateSerializer, CarrinhoRemoverItemSerializer, CarrinhoAlterarQuantidadeSerializer, CancelarPedidoSerializer
from django.db import transaction
from apps.core.pagination import DefaultPagination
from rest_framework.decorators import action
from django.db.models import Sum, Count, Avg
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(tags=["Carrinho"])
class CarrinhoViewSet(viewsets.ModelViewSet):
    """
    Endpoint para gerenciamento do carrinho de compras do usuário autenticado.
    O usuário só pode ter um carrinho por vez.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Carrinho.objects.none()

        return Carrinho.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Retorna o carrinho do usuário, criando automaticamente se necessário.
        """
        carrinho, _ = Carrinho.objects.get_or_create(user=self.request.user)
        return carrinho

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", {})
        kwargs["context"]["request"] = self.request
        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        if self.action == "create":
            return CarrinhoAdicionarItemSerializer

        if self.action == "remover_item":
            return CarrinhoRemoverItemSerializer

        if self.action == "atualizar_quantidade":
            return CarrinhoAlterarQuantidadeSerializer

        return CarrinhoSerializer


    @swagger_auto_schema(
        tags=["Carrinho"],
        operation_description=(
            "Gerencia o carrinho de compras do usuário autenticado.\n\n"
            "**Funcionalidades principais:**\n"
            "- O carrinho é criado automaticamente caso não exista\n"
            "- Listar todos os itens do carrinho\n"
            "- Adicionar itens\n"
            "- Remover itens\n"
            "- Atualizar quantidade de um item\n\n"
            "**Regras importantes:**\n"
            "- O usuário só pode ter itens de **uma loja por vez** no carrinho\n"
            "- A quantidade solicitada deve respeitar o estoque disponível\n"
        )
    )
    def list(self, request, *args, **kwargs):
        carrinho = self.get_object()
        serializer = self.get_serializer(carrinho)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Carrinho"],
        operation_description=(
            "Adiciona um item ao carrinho do usuário.\n\n"
            "- Se o item já existir, sua quantidade será incrementada\n"
            "- Só é permitido adicionar itens de **uma loja por vez**\n"
            "- A operação falha caso a quantidade desejada exceda o estoque\n"
        ),
        request_body=CarrinhoAdicionarItemSerializer,
        responses={
            201: openapi.Response("Item adicionado com sucesso", CarrinhoItemSerializer),
            400: "Estoque insuficiente ou operação inválida",
            404: "Produto não encontrado"
        }
    )
    def create(self, request, *args, **kwargs):
        carrinho = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        produto = serializer.validated_data["produto"]
        quantidade = serializer.validated_data["quantidade"]

        if carrinho.items.exists():
            item_existente = carrinho.items.first()
            if item_existente.produto.loja != produto.loja:
                return Response(
                    {
                        "detail": (
                            "Você só pode adicionar itens de uma loja por vez. "
                            f"Seu carrinho atual contém itens da loja '{item_existente.produto.loja.nome}'. "
                            f"Esvazie o carrinho para comprar em '{produto.loja.nome}'."
                        )
                    }
                )

        if quantidade > produto.quantidade:
            return Response(
                {"detail": f"Estoque insuficiente. Disponível: {produto.quantidade}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item, created = CarrinhoItem.objects.get_or_create(
            carrinho=carrinho,
            produto=produto,
            defaults={"quantidade": quantidade}
        )

        if not created:
            if item.quantidade + quantidade > produto.quantidade:
                return Response(
                    {"detail": f"Quantidade total excede o estoque. Disponível: {produto.quantidade}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.quantidade += quantidade
            item.save()

        return Response(
            CarrinhoItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        tags=["Carrinho"],
        method="post",
        operation_description="Remove um item do carrinho. É necessário informar o produto.",
        request_body=CarrinhoRemoverItemSerializer,
        responses={
            204: "Item removido com sucesso",
            400: "Requisição inválida",
            404: "Item não encontrado no carrinho"
        }
    )
    @action(detail=False, methods=["post"], url_path="remover-item")
    def remover_item(self, request):
        carrinho = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        produto = serializer.validated_data["produto"]

        item = CarrinhoItem.objects.filter(carrinho=carrinho, produto=produto).first()

        if not item:
            return Response(
                {"detail": "Produto não encontrado no carrinho."},
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @swagger_auto_schema(
        tags=["Carrinho"],
        method="post",
        operation_description=(
            "Atualiza a quantidade de um item no carrinho.\n"
            "- A operação falha se exceder o estoque disponível."
        ),
        request_body=CarrinhoAlterarQuantidadeSerializer,
        responses={
            200: openapi.Response("Quantidade atualizada com sucesso", CarrinhoItemSerializer),
            400: "Estoque insuficiente",
            404: "Item não encontrado"
        }
    )
    @action(detail=False, methods=["post"], url_path="atualizar-quantidade")
    def atualizar_quantidade(self, request):
        carrinho = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        produto = serializer.validated_data["produto"]
        nova_qtd = serializer.validated_data["quantidade"]

        item = CarrinhoItem.objects.filter(carrinho=carrinho, produto=produto).first()

        if not item:
            return Response(
                {"detail": "Item não encontrado no carrinho."},
                status=status.HTTP_404_NOT_FOUND
            )

        if nova_qtd > produto.quantidade:
            return Response(
                {"detail": f"Estoque insuficiente. Disponível: {produto.quantidade}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantidade = nova_qtd
        item.save()

        return Response(
            CarrinhoItemSerializer(item, context={"request": request}).data
        )
    

@swagger_auto_schema(tags=["Pedidos"])
class PedidoViewSet(viewsets.ModelViewSet):
    """
    Endpoint responsável por listar e criar pedidos do usuário autenticado.

    Operações:
    - GET /pedidos/ → lista todos os pedidos do usuário.
    - POST /pedidos/ → cria um novo pedido a partir do carrinho.
    - GET /pedidos/{id}/ → visualiza os detalhes de um pedido.
    """

    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]


    @swagger_auto_schema(
        tags=["Pedidos"],
        operation_summary="Listar pedidos do usuário autenticado",
        operation_description="Retorna a lista de pedidos feitos pelo usuário, ordenados do mais recente para o mais antigo.",
        responses={200: PedidoSerializer(many=True)}
    )
    def get_queryset(self):
        return Pedido.objects.filter(user=self.request.user).order_by("-criado_em")


    @swagger_auto_schema(
        tags=["Pedidos"],
        operation_summary="Criar pedido a partir do carrinho",
        operation_description="Gera um pedido com base nos itens do carrinho do usuário autenticado. "
                              "Após criar o pedido, o carrinho é esvaziado.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "metodo_pagamento": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID do método de pagamento escolhido."
                )
            },
            required=["metodo_pagamento"]
        ),
        responses={
            201: openapi.Response("Pedido criado com sucesso", PedidoSerializer),
            400: "Carrinho vazio ou método de pagamento inválido"
        }
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user = request.user
        metodo_pagamento_id = request.data.get("metodo_pagamento")
        try:
            endereco = Endereco.objects.get(user=user)
        except Endereco.DoesNotExist:
            return Response(
                {"detail": "É necessário cadastrar um endereço de entrega antes de finalizar o pedido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        carrinho = Carrinho.objects.filter(user=user).first()
        if not carrinho or not carrinho.items.exists():
            return Response(
                {"detail": "Carrinho vazio."},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        return Response(
            PedidoSerializer(pedido).data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        tags=["Pedidos"],
        operation_summary="Detalhes de um pedido",
        operation_description="Retorna todas as informações de um pedido específico do usuário.",
        responses={200: PedidoSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

@swagger_auto_schema(tags=["Pagamento"])
class MetodoPagamentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pagamento.objects.all()
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags = ["Pagamento"],
        operation_summary="Listar métodos de pagamento",
        operation_description=(
            "Retorna todos os métodos de pagamento disponíveis no sistema. "
            "Este endpoint não exige autenticação."
        ),
        responses={
            200: openapi.Response(
                description="Lista de métodos de pagamento",
                schema=PagamentoSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags = ["Pagamento"],
        operation_summary="Detalhar método de pagamento",
        operation_description=(
            "Retorna detalhes de um método de pagamento específico pelo seu ID. "
        ),
        responses={
            200: openapi.Response(
                description="Método de pagamento encontrado",
                schema=PagamentoSerializer()
            ),
            404: "Método de pagamento não encontrado"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
        
@swagger_auto_schema(tags=["Histórico Usuário"])
class HistoricoPedidoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Pedido.objects.none()

        status_visiveis = [
            "entregue", "Entregue", 
            "cancelado", "Cancelado", 
            "pendente", "Pendente", 
            "a caminho", "A caminho", "A Caminho",
            "preparando", "Preparando"
        ]

        return Pedido.objects.filter(
            user=self.request.user,
            status__in=status_visiveis
        ).order_by("-criado_em")

    def get_serializer_class(self):
        if self.action == "cancelar":
            return CancelarPedidoSerializer
        return PedidoSerializer

    def get_serializer(self, *args, **kwargs):
        if self.action == "cancelar":
            kwargs.setdefault("user", self.request.user)
        return super().get_serializer(*args, **kwargs)

    @swagger_auto_schema(
        tags=["Histórico Usuário"],
        operation_summary="Detalhar pedido específico",
        responses={200: PedidoSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["Histórico Usuário"],
        method="post",
        operation_summary="Cancelar um pedido",
        operation_description="Selecione o ID do pedido que deseja cancelar.",
        request_body=CancelarPedidoSerializer,
        responses={
            200: PedidoSerializer, 
            400: "Erro: Pedido inválido ou não pertence ao usuário"
        }
    )
    @action(detail=False, methods=["post"], url_path="cancelar")
    def cancelar(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pedido = serializer.validated_data["pedido"]
        pedido.status = "cancelado" 
        pedido.save()

        return Response(PedidoSerializer(pedido).data)
    
@swagger_auto_schema(tags=["Histórico Loja"])
class HistoricoLojaViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "put", "head", "options"]
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.action in ["partial_update", "update"]:
            return AtualizarStatusPedidoSerializer
        return PedidoLojaSerializer

    def get_queryset(self):
        payload = self.request.auth or {}
        loja_id = payload.get("loja_id")

        if not loja_id:
            return Pedido.objects.none()

        return Pedido.objects.filter(loja_id=loja_id).order_by("-criado_em")

    @swagger_auto_schema(
        tags = ["Histórico Loja"],
        operation_summary="Listar pedidos da loja",
        responses={200: PedidoLojaSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags = ["Histórico Loja"],
        operation_summary="Detalhar um pedido",
        responses={200: PedidoLojaSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["Histórico Loja"],
        operation_summary="Atualizar status do pedido (parcial)",
        operation_description="Permite atualizar parcialmente o status de um pedido da loja.",
        request_body=AtualizarStatusPedidoSerializer,
        responses={200: PedidoLojaSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        pedido = self.get_object()
        payload = request.auth or {}
        loja_id = payload.get("loja_id")

        if not loja_id or pedido.loja_id != loja_id:
            return Response(
                {"detail": "Usuário não pertence à loja do pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AtualizarStatusPedidoSerializer(pedido, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        pedido.status = serializer.validated_data["status"]
        pedido.save()

        return Response(PedidoLojaSerializer(pedido).data)
    
    @swagger_auto_schema(
        tags=["Histórico Loja"],
        operation_summary="Atualizar status do pedido (completo)",
        operation_description="Atualização completa do status de um pedido da loja.",
        request_body=AtualizarStatusPedidoSerializer,
        responses={200: PedidoLojaSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

        
@swagger_auto_schema(tags=["Pedidos"])
class PedidoLojaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoLojaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination


    @swagger_auto_schema(
        tags=["Pedidos"],
        operation_summary="Listar pedidos da loja",
        operation_description=(
            "Retorna todos os pedidos associados à loja definida no token JWT "
            "(`loja_id`). Se o token não contiver `loja_id`, retorna uma lista vazia."
        ),
        responses={200: PedidoLojaSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        payload = self.request.auth or {}
        loja_id = payload.get("loja_id")

        if not loja_id:
            return Pedido.objects.none()

        return Pedido.objects.filter(loja_id=loja_id).order_by("-criado_em")


    @swagger_auto_schema(
        tags=["Pedidos"],
        operation_summary="Detalhar pedido da loja",
        operation_description=(
            "Retorna os detalhes de um pedido que pertence à loja do token JWT (`loja_id`). "
            "Se não pertencer à loja, retorna erro."
        ),
        responses={
            200: PedidoLojaSerializer(),
            404: "Pedido não encontrado"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

 
    @swagger_auto_schema(
        tags=["Pedidos"],
        operation_summary="Atualizar status do pedido",
        operation_description=(
            "Atualiza o status de um pedido pertencente à loja identificada pelo token JWT (`loja_id`). "
            "O corpo da requisição deve conter apenas o novo status."
        ),
        request_body=AtualizarStatusPedidoSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"mensagem": openapi.Schema(type=openapi.TYPE_STRING)}
            ),
            400: "Dados inválidos",
            403: "Acesso negado",
            404: "Pedido não encontrado"
        }
    )
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
    
@swagger_auto_schema(tags=["Pedidos"])
class MeusPedidosViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoints do cliente para visualizar e cancelar pedidos.
    """
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags = ["Pedidos"],
        operation_summary="Listar pedidos do cliente",
        responses={200: PedidoSerializer(many=True)}
    )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Pedido.objects.none()

        return Pedido.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        tags = ["Pedidos"],
        method="patch",
        operation_summary="Cancelar pedido",
        operation_description=(
            "Cancela o pedido do usuário, desde que ainda esteja em um status "
            "que permita cancelamento (ex: pendente ou preparando)."
        ),
        responses={
            200: openapi.Response("Pedido cancelado", PedidoSerializer),
            400: "Pedido não pode ser cancelado",
            404: "Pedido não encontrado"
        }
    )
    @action(detail=True, methods=["PATCH"], url_path="cancelar")
    def cancelar(self, request, *, pk=None):
        pedido = self.get_object()

        status_cancelaveis = ["pendente", "preparando"]

        if pedido.status not in status_cancelaveis:
            return Response(
                {"erro": "Este pedido não pode mais ser cancelado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        pedido.status = "cancelado"
        pedido.save()

        return Response(PedidoSerializer(pedido).data)


@swagger_auto_schema(tags=["Endereço"])
class EnderecoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDonoeReadOnly]


    @swagger_auto_schema(
        tags = ["Endereço"],
        operation_summary="Listar endereços do usuário",
        operation_description="Retorna todos os endereços cadastrados pelo usuário autenticado.",
        responses={200: EnderecoSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Endereco.objects.none()

        return Endereco.objects.filter(user=self.request.user)


    def get_serializer_class(self):
        if self.action == "create":
            return EnderecoCreateSerializer
        return EnderecoSerializer


    @swagger_auto_schema(
        tags = ["Endereço"],    
        operation_summary="Criar novo endereço",
        operation_description="Adiciona um novo endereço ao perfil do usuário autenticado.",
        request_body=EnderecoCreateSerializer,
        responses={
            201: EnderecoSerializer,
            400: "Erro na validação dos dados"
        }
    )
    def create(self, request, *args, **kwargs):
        if Endereco.objects.filter(user=request.user).exists():
                    return Response(
                        {
                            "detail": "Você já possui um endereço cadastrado. "
                                      "Edite o endereço existente"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


    @swagger_auto_schema(
        tags = ["Endereço"],
        operation_summary="Detalhar um endereço",
        operation_description="Retorna os dados completos de um endereço específico do usuário.",
        responses={200: EnderecoSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


    @swagger_auto_schema(
        tags = ["Endereço"],
        operation_summary="Atualizar um endereço",
        operation_description="Atualiza todos os campos de um endereço já cadastrado.",
        request_body=EnderecoSerializer,
        responses={
            200: EnderecoSerializer(),
            400: "Dados inválidos"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


    @swagger_auto_schema(
        tags = ["Endereço"],
        operation_summary="Atualização parcial de endereço",
        operation_description="Atualiza apenas alguns campos de um endereço do usuário.",
        request_body=EnderecoSerializer,
        responses={
            200: EnderecoSerializer(),
            400: "Dados inválidos"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags = ["Endereço"],
        operation_summary="Excluir um endereço",
        operation_description="Remove um endereço do usuário definitivamente.",
        responses={204: "Endereço removido com sucesso"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

@swagger_auto_schema(tags=["Pagamento"])
class PagamentoViewSet(viewsets.ModelViewSet):
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Pagamento.objects.none()

        return Pagamento.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        tags = ["Pagamento"],
        operation_summary="Listar métodos de pagamento",
        operation_description="Retorna todos os métodos de pagamento cadastrados pelo usuário.",
        responses={200: PagamentoSerializer(many=True)},
    )
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(
        tags = ["Pagamento"],            
        operation_summary="Criar método de pagamento",
        request_body=PagamentoSerializer,
        responses={201: PagamentoSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags = ["Pagamento"],
        operation_summary="Atualizar método de pagamento",
        request_body=PagamentoSerializer,
        responses={200: PagamentoSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags = ["Pagamento"],
        operation_summary="Atualizar parcialmente",
        request_body=PagamentoSerializer,
        responses={200: PagamentoSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags = ["Pagamento"],
        operation_summary="Remover método de pagamento",
        operation_description="Remove logicamente (ativo=False).",
        responses={200: openapi.Response("Método de pagamento removido.")},
    )
    def destroy(self, request, *args, **kwargs):
        pagamento = self.get_object()
        pagamento.ativo = False
        pagamento.save()
        return Response({"mensagem": "Método de pagamento removido."})

    @swagger_auto_schema(
        tags = ["Pagamento"],
        method="get",
        operation_summary="Listar métodos de pagamento ativos (dropdown)",
        responses={200: MetodoPagamentoSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["GET"],
        url_path="listar",
        serializer_class=MetodoPagamentoSerializer,
    )
    def listar_metodos(self, request):
        metodos = Pagamento.objects.filter(user=request.user, ativo=True)
        serializer = MetodoPagamentoSerializer(metodos, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags = ["Pagamento"],
        method="post",
        operation_summary="Finalizar pagamento",
        operation_description="Realiza o pagamento dos pedidos selecionados.",
        request_body=FinalizarPagamentoSerializer,
        responses={
            201: openapi.Response(
                description="Pagamento finalizado",
                examples={
                    "exemplo": {
                        "sucesso": True,
                        "mensagem": "Pagamento concluído com sucesso.",
                        "pedidos": [1, 5, 7]
                    }
                }
            )
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        url_path="pagar",
        serializer_class=FinalizarPagamentoSerializer,
    )
    def pagar(self, request):
        serializer = FinalizarPagamentoSerializer(
            data=request.data,
            context={"request": request},
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


@swagger_auto_schema(tags=["Faturamento"])
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

    @swagger_auto_schema(
        tags=["Faturamento"],
        method="get",
        operation_summary="Consultar faturamento por período (GET)",
        operation_description=(
            "Retorna o faturamento da loja do usuário autenticado "
            "com base no intervalo de datas informado como query params.\n\n"
            "**Atenção:** somente pedidos com status `entregue` são considerados."
        ),
        manual_parameters=[
            openapi.Parameter(
                "data_inicial",
                openapi.IN_QUERY,
                description="Data inicial no formato AAAA-MM-DD",
                type=openapi.TYPE_STRING,
                format="date",
                required=True
            ),
            openapi.Parameter(
                "data_final",
                openapi.IN_QUERY,
                description="Data final no formato AAAA-MM-DD",
                type=openapi.TYPE_STRING,
                format="date",
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="Resumo de faturamento calculado com sucesso",
                examples={
                    "application/json": {
                        "periodo": {
                            "data_inicial": "2025-01-01",
                            "data_final": "2025-01-31"
                        },
                        "resumo": {
                            "total_faturado": 1520.50,
                            "total_pedidos": 12,
                            "ticket_medio": 126.70
                        }
                    }
                }
            )
        }
    )
    @swagger_auto_schema(
        tags=["Faturamento"],
        method="post",
        operation_summary="Consultar faturamento por período (POST)",
        operation_description=(
            "Recebe o intervalo de datas no corpo da requisição e retorna "
            "o faturamento da loja do usuário.\n\n"
            "Útil quando se deseja enviar dados via JSON em vez de query params.\n\n"
            "**Somente pedidos com status `entregue` são contabilizados.**"
        ),
        request_body=FaturamentoFiltroSerializer,
        responses={
            200: openapi.Response(
                description="Resumo de faturamento calculado com sucesso",
                examples={
                    "application/json": {
                        "periodo": {
                            "data_inicial": "2025-02-01",
                            "data_final": "2025-02-28"
                        },
                        "resumo": {
                            "total_faturado": 2190.30,
                            "total_pedidos": 15,
                            "ticket_medio": 146.02
                        }
                    }
                }
            ),
            400: "Erro de validação nos campos enviados"
        }
    )
    @action(detail=False, methods=["get", "post"])
    def periodo(self, request):
        dados = request.query_params if request.method == "GET" else request.data
        serializer = self.get_serializer(data=dados)
        serializer.is_valid(raise_exception=True)

        data_inicial = serializer.validated_data["data_inicial"]
        data_final = serializer.validated_data["data_final"]
        claims = request.auth or {}
        loja_id = claims.get("loja_id")

        if not loja_id:
            return Response(
                {"detail": "Apenas lojas podem acessar o faturamento."},
                status=status.HTTP_403_FORBIDDEN
            )

        pedidos = Pedido.objects.filter(
            loja_id=loja_id,
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
