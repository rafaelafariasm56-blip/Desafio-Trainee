from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from apps.users.models import User
from apps.core.models import Produto, LojaPerfil
from apps.users.serializers import UserSerializer, UserRegisterSerializer
from apps.users.permissions import IsLoja, IsClient, IsDonoeReadOnly
from apps.core.serializers import ProdutoSerializer, CardapioSerializer, CardapioItemSerializer
from apps.pedidos.models import Pedido
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


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'descricao', 'loja__nome']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsDonoeReadOnly]
    def perform_create(self, serializer):
        loja = LojaPerfil.objects.get(user=self.request.user)
        serializer.save(loja=loja)


class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]