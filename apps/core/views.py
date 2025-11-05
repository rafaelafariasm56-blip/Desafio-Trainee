from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions

from apps.users.models import User
from apps.core.models import Produto, LojaPerfil, Cardapio
from apps.users.serializers import UserSerializer, UserRegisterSerializer
from apps.users.permissions import IsDonoeReadOnly
from apps.core.serializers import ProdutoSerializer, CardapioSerializer, LojaSerializer
from apps.pedidos.serializers import PedidoSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de usuários (clientes e lojas).
    Permissões variam conforme o tipo de usuário.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "nome"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsDonoeReadOnly]
        else:
            permission_classes = [permissions.AllowAny]
        return [perm() for perm in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegisterSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return User.objects.none()
        if getattr(user, "is_establishment", False):
            return User.objects.filter(loja=False)
        return User.objects.filter(loja=True)


class ProdutoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint público de produtos.
    Apenas leitura (clientes podem ver o que as lojas oferecem).
    """
    queryset = Produto.objects.filter(active=True)
    serializer_class = ProdutoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'descricao', 'loja__nome']
    ordering_fields = ['criada_em', 'nome']
    permission_classes = [permissions.AllowAny]


class LojaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint público de lojas abertas.
    """
    queryset = LojaPerfil.objects.filter(aberta=True)
    serializer_class = LojaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'endereco', 'user__username']
    ordering_fields = ['nome']
    permission_classes = [permissions.AllowAny]


class CardapioViewSet(viewsets.ModelViewSet):
    serializer_class = CardapioSerializer
    queryset = Cardapio.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "loja"):
            return Cardapio.objects.filter(loja=user.loja)
        raise PermissionDenied("Apenas lojas podem acessar o cardápio.")

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, "loja"):
            serializer.save(loja=user.loja)
        else:
            raise PermissionDenied("Apenas lojas podem cadastrar produtos.")
