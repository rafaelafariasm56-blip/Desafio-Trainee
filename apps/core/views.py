from rest_framework import viewsets, permissions, filters, serializers, generics
from rest_framework.exceptions import PermissionDenied
from apps.users.models import Pagamento
from apps.pedidos.serializers import PagamentoSerializer
from apps.core.models import LojaPerfil, Produto
from apps.core.serializers import LojaSerializer, ProdutoSerializer, ProdutoLeituraSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Produto, LojaPerfil
from .serializers import ProdutoSerializer
from apps.users.permissions import IsLoja
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.filter(active=True, disponivel=True)
    serializer_class = ProdutoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "descricao", "loja__nome"]
    ordering_fields = ["criada_em", "nome", "preco"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsLoja()]

    def get_queryset(self):
        claims = self.request.auth
        if not claims or not claims.get("is_loja"):
            return Produto.objects.filter(active=True, disponivel=True)
        loja_id = claims.get("loja_id")
        if loja_id:
            return Produto.objects.filter(loja_id=loja_id)
        return Produto.objects.filter(active=True, disponivel=True)

    def get_serializer_class(self):
        claims = self.request.auth
        if not claims or not claims.get("is_loja"):
            return ProdutoLeituraSerializer
        return self.serializer_class

    @swagger_auto_schema(
        operation_description="Cria um novo produto. Apenas lojas autenticadas podem criar.",
        request_body=ProdutoSerializer,
        responses={
            201: ProdutoSerializer,
            403: "Apenas lojas podem criar produtos.",
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Lista todos os produtos ativos e disponíveis. Usuários normais recebem visualização limitada.",
        manual_parameters=[
            openapi.Parameter(
                'search', openapi.IN_QUERY, description="Busca por nome, descrição ou loja", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering', openapi.IN_QUERY, description="Ordenação por 'criada_em', 'nome' ou 'preco'", type=openapi.TYPE_STRING
            ),
        ],
        responses={200: ProdutoLeituraSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Recupera um produto específico pelo ID.",
        responses={200: ProdutoLeituraSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Deleta um produto. Apenas lojas que possuem o produto podem deletar.",
        responses={204: "Produto deletado com sucesso", 
                   403: "Permissão negada"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Atualiza um produto existente. Apenas a loja que criou o produto pode atualizar.",
        request_body=ProdutoSerializer,
        responses={200: ProdutoSerializer, 
                   403: "Permissão negada"}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Atualização parcial de um produto.",
        request_body=ProdutoSerializer,
        responses={200: ProdutoSerializer, 
                   403: "Permissão negada"}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class PagamentoListCreateView(generics.ListCreateAPIView):
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Lista métodos de pagamento do usuário logado.", responses={200: PagamentoSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Cria um novo método de pagamento para o usuário logado.", request_body=PagamentoSerializer, responses={201: PagamentoSerializer})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        claims = self.request.auth
        user_id = claims.get("user_id")
        return Pagamento.objects.filter(user_id=user_id)

    def perform_create(self, serializer):
        claims = self.request.auth
        user_id = claims.get("user_id")
        serializer.save(user_id=user_id)

class PagamentoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        claims = self.request.auth
        user_id = claims.get("user_id")
        return Pagamento.objects.filter(user_id=user_id)

    @swagger_auto_schema(operation_description="Recupera um método de pagamento específico do usuário logado.", responses={200: PagamentoSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Atualiza um método de pagamento do usuário logado.", request_body=PagamentoSerializer, responses={200: PagamentoSerializer})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Atualização parcial de um método de pagamento do usuário logado.", request_body=PagamentoSerializer, responses={200: PagamentoSerializer})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Deleta um método de pagamento do usuário logado.", responses={204: "Pagamento deletado com sucesso"})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)



class LojaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LojaPerfil.objects.filter(aberta=True)
    serializer_class = LojaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "endereco", "user__username"]
    ordering_fields = ["nome"]
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Lista todas as lojas abertas.",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Busca por nome, endereço ou username da loja", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Ordenação por nome da loja", type=openapi.TYPE_STRING),
        ],
        responses={200: LojaSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Recupera uma loja específica pelo ID.",
        responses={200: LojaSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CardapioViewSet(viewsets.ModelViewSet):
    serializer_class = ProdutoSerializer

    def get_permissions(self):
        claims = self.request.auth
        if not claims or not claims.get("is_loja"):
            raise PermissionDenied("Apenas lojas podem acessar o cardápio.")
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        claims = self.request.auth
        loja_id = claims.get("loja_id")
        if not loja_id:
            return Produto.objects.none()
        return Produto.objects.filter(loja_id=loja_id)

    @swagger_auto_schema(operation_description="Lista produtos do cardápio da loja logada.", responses={200: ProdutoSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Recupera um produto específico do cardápio.", responses={200: ProdutoSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Cria um produto no cardápio da loja logada.", request_body=ProdutoSerializer, responses={201: ProdutoSerializer, 403: "Permissão negada"})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Atualiza um produto do cardápio.", request_body=ProdutoSerializer, responses={200: ProdutoSerializer, 403: "Permissão negada"})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Atualização parcial de um produto do cardápio.", request_body=ProdutoSerializer, responses={200: ProdutoSerializer, 403: "Permissão negada"})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Deleta um produto do cardápio da loja logada.", responses={204: "Produto deletado com sucesso", 403: "Permissão negada"})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
