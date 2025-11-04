from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from apps.users.models import User
from apps.core.models import Produto, LojaPerfil, Cardapio
from apps.users.serializers import UserSerializer, UserRegisterSerializer
from apps.users.permissions import IsLoja, IsClient, IsDonoeReadOnly
from apps.core.serializers import ProdutoSerializer, CardapioSerializer, CardapioItemSerializer, LojaSerializer
from apps.pedidos.serializers import PedidoSerializer
from apps.core.permissions import ELojaOuSomenteLeitura

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
            # Qualquer usuário autenticado pode ver perfis (leitura)
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Só o próprio usuário pode editar ou deletar o perfil
            permission_classes = [permissions.IsAuthenticated, IsDonoeReadOnly]
        else:
            # Outras ações (create, etc)
            permission_classes = [permissions.AllowAny]
        return [perm() for perm in permission_classes]

    def get_serializer_class(self):
        #Usa o serializer de registro ao criar um novo usuário.
        if self.action == "create":
            return UserRegisterSerializer
        return UserSerializer

    def get_queryset(self):
        #Define o conjunto de usuários visível conforme o tipo.
        user = self.request.user

        # Users não autenticados não veem nada
        if not user.is_authenticated:
            return User.objects.none()
        
        #Loja só vê cliente
        if user.is_establishment:
            return User.objects.filter(loja=False)

        # Cliente só vê loja
        return User.objects.filter(loja=True)


class ProdutoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Produto.objects.filter(active=True)
    serializer_class = ProdutoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'descricao', 'loja__nome']
    ordering_fields = ['criada_em', 'nome']
    permission_classes = [permissions.AllowAny]


class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]


class LojaViewSet(viewsets.ReadOnlyModelViewSet):
 
    queryset = LojaPerfil.objects.filter(aberta=True)
    serializer_class = LojaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'endereco', 'user__username']
    ordering_fields = ['nome']
    permission_classes = [permissions.AllowAny]

class CardapioViewSet(viewsets.ModelViewSet):
    serializer_class = CardapioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, ELojaOuSomenteLeitura]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'loja__username']

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated or not user.loja:
            return Cardapio.objects.all()

        return Cardapio.objects.filter(loja=user)

    def perform_create(self, serializer):
        serializer.save(loja=self.request.user)