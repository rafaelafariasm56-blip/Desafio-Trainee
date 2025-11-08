from rest_framework import viewsets, permissions, filters, generics
from rest_framework.exceptions import PermissionDenied
from apps.users.models import Pagamento
from apps.users.serializers import PagamentoSerializer
from apps.core.models import LojaPerfil, Produto, Cardapio
from apps.core.serializers import LojaSerializer, ProdutoSerializer, CardapioSerializer
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response


class ProdutoViewSet(viewsets.ModelViewSet):
    #Listagem e criação de produtos de loja.
    queryset = Produto.objects.filter(active=True)
    serializer_class = ProdutoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "descricao", "loja__nome"]
    ordering_fields = ["criada_em", "nome", "preco"]

    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ["list", "retrieve"] else [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.loja:
            raise PermissionDenied("Apenas perfis de loja podem adicionar produtos.")
        loja = getattr(user, "lojaperfil", None)
        if not loja:
            raise PermissionDenied("Perfil de loja não encontrado. Crie um perfil antes de adicionar produtos.")
        serializer.save(loja=loja)

class PagamentoListCreateView(generics.ListCreateAPIView):
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pagamento.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PagamentoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pagamento.objects.filter(user=self.request.user)


class LojaViewSet(viewsets.ReadOnlyModelViewSet):
    #Visualização de lojas (somente leitura).
    queryset = LojaPerfil.objects.filter(aberta=True)
    serializer_class = LojaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "endereco", "user__username"]
    ordering_fields = ["nome"]
    permission_classes = [permissions.AllowAny]


class CardapioViewSet(viewsets.ModelViewSet):
    #Visualização e gerenciamento de cardápio.
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.loja and hasattr(user, "lojaperfil"):
            return Produto.objects.filter(loja=user.lojaperfil)
        return Produto.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        loja = getattr(user, "lojaperfil", None)
        if not user.loja or not loja:
            raise PermissionDenied("Apenas perfis de loja podem adicionar produtos.")
        serializer.save(loja=loja)
