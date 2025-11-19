from rest_framework import viewsets, permissions, filters, generics
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.users.models import Pagamento
from apps.pedidos.serializers import PagamentoSerializer
from apps.core.models import LojaPerfil, Produto
from apps.core.serializers import LojaSerializer, ProdutoSerializer, ProdutoLeituraSerializer
from apps.users.permissions import IsLoja
from .pagination import DefaultPagination

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.filter(active=True, disponivel=True)
    serializer_class = ProdutoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    pagination_class = DefaultPagination 
    search_fields = ["nome", "descricao", "loja__nome"]
    ordering_fields = ["criada_em", "nome", "preco"]

    def get_permissions(self):
        claims = self.request.auth or {}
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsLoja()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Produto.objects.none()

        claims = self.request.auth or {}
        if not claims.get("is_loja"):
            return Produto.objects.filter(active=True, disponivel=True)

        loja_id = claims.get("loja_id")
        if loja_id:
            return Produto.objects.filter(loja_id=loja_id)

        return Produto.objects.filter(active=True, disponivel=True)

    def get_serializer_class(self):
        claims = self.request.auth or {}
        if not claims.get("is_loja"):
            return ProdutoLeituraSerializer
        return ProdutoSerializer

    @swagger_auto_schema(
        operation_summary="Criar um novo produto",
        operation_description=(
            "Cria um novo produto no sistema. "
            "Somente lojas autenticadas podem criar produtos. "
            "Os dados devem seguir o `ProdutoSerializer`."
        ),
        request_body=ProdutoSerializer,
        tags=["Produtos"],
        responses={
            201: ProdutoSerializer,
            403: "Apenas lojas podem criar produtos."
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Listar produtos",
        operation_description=(
            "Lista todos os produtos ativos e disponíveis. "
            "A busca pode ser feita por nome, descrição ou nome da loja. "
            "A ordenação pode ser feita por data de criação, nome ou preço."
        ),
        manual_parameters=[
            openapi.Parameter(
                "search", openapi.IN_QUERY,
                description="Busca por nome, descrição ou loja",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "ordering", openapi.IN_QUERY,
                description="Ordenação por 'criada_em', 'nome' ou 'preco'",
                type=openapi.TYPE_STRING
            ),
        ],
        tags=["Produtos"],
        responses={200: ProdutoLeituraSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Recuperar produto",
        operation_description="Retorna os detalhes de um produto pelo ID.",
        tags=["Produtos"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir produto",
        operation_description="Deleta permanentemente um produto da loja autenticada.",
        tags=["Produtos"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar produto (PUT)",
        operation_description=(
            "Atualiza completamente os dados de um produto da loja. "
            "Todos os campos serão substituídos."
        ),
        tags=["Produtos"],
        request_body=ProdutoSerializer
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente produto (PATCH)",
        operation_description=(
            "Atualiza parcialmente os dados de um produto, modificando apenas "
            "os campos enviados no corpo da requisição."
        ),
        tags=["Produtos"],
        request_body=ProdutoSerializer
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)



@swagger_auto_schema(tags=["Pagamentos"])
class PagamentoListCreateView(generics.ListCreateAPIView):
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Pagamento.objects.none()

        claims = self.request.auth or {}
        user_id = claims.get("user_id")
        return Pagamento.objects.filter(user_id=user_id)

    def perform_create(self, serializer):
        claims = self.request.auth or {}
        user_id = claims.get("user_id")
        serializer.save(user_id=user_id)

    @swagger_auto_schema(tags=["Pagamentos"], operation_description="Lista métodos de pagamento.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Pagamentos"], operation_description="Cria um método de pagamento.", request_body=PagamentoSerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


@swagger_auto_schema(tags=["Pagamentos"])
class PagamentoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Pagamento.objects.none()

        claims = self.request.auth or {}
        user_id = claims.get("user_id")
        return Pagamento.objects.filter(user_id=user_id)

    @swagger_auto_schema(tags=["Pagamentos"], operation_description="Recupera um método de pagamento por ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Pagamentos"], operation_description="Atualiza método de pagamento.", request_body=PagamentoSerializer)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Pagamentos"], operation_description="Atualização parcial.", request_body=PagamentoSerializer)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Pagamentos"], operation_description="Deleta método de pagamento.")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class LojaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LojaPerfil.objects.filter(aberta=True)
    serializer_class = LojaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "endereco", "user__username"]
    ordering_fields = ["nome"]
    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LojaPerfil.objects.none()
        return LojaPerfil.objects.filter(aberta=True)

    @swagger_auto_schema(
        operation_summary="Listar lojas abertas",
        operation_description=(
            "Retorna a lista de todas as lojas que estão marcadas como abertas no sistema. "
            "É possível realizar busca por nome, endereço ou nome de usuário do dono da loja, "
            "além de permitir ordenação por nome."
        ),
        tags=["Lojas"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar loja por ID",
        operation_description=(
            "Retorna as informações completas de uma loja específica, desde que ela esteja aberta. "
            "A busca é feita através do ID da loja."
        ),
        tags=["Lojas"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class CardapioViewSet(viewsets.ModelViewSet):
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        claims = self.request.auth or {}
        if not claims.get("is_loja"):
            raise PermissionDenied("Apenas lojas podem acessar o cardápio.")
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Produto.objects.none()

        claims = self.request.auth or {}
        loja_id = claims.get("loja_id")

        if not loja_id:
            return Produto.objects.none()

        return Produto.objects.filter(loja_id=loja_id)

    @swagger_auto_schema(
        operation_summary="Listar produtos do cardápio",
        operation_description=(
            "Retorna todos os produtos cadastrados no cardápio da loja autenticada."
        ),
        tags=["Cardápio"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar produto do cardápio",
        operation_description=(
            "Retorna os detalhes de um produto específico pertencente à loja."
        ),
        tags=["Cardápio"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar produto no cardápio",
        operation_description=(
            "Cria um novo item no cardápio da loja autenticada."
        ),
        request_body=ProdutoSerializer,
        tags=["Cardápio"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar produto",
        operation_description=(
            "Atualiza todos os dados de um produto do cardápio."
        ),
        request_body=ProdutoSerializer,
        tags=["Cardápio"]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente produto",
        operation_description=(
            "Atualiza apenas os campos enviados no corpo da requisição."
        ),
        request_body=ProdutoSerializer,
        tags=["Cardápio"]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir produto",
        operation_description=(
            "Remove um produto do cardápio da loja autenticada."
        ),
        tags=["Cardápio"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)