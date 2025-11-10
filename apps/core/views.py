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
from .permissions import ELojaOuSomenteLeitura

from rest_framework import viewsets, permissions, filters, serializers
from rest_framework.exceptions import PermissionDenied
from .models import Produto, LojaPerfil
from .serializers import ProdutoSerializer


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.filter(disponivel=True, active=True)
    serializer_class = ProdutoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "descricao", "loja__nome"]
    ordering_fields = ["criada_em", "nome", "preco"]

    def get_queryset(self):
        user = self.request.user
        qs = Produto.objects.filter(active=True, disponivel=True)

        if not user.is_authenticated:
            return qs  

        if hasattr(user, "lojaperfil"):
            return Produto.objects.filter(loja=user.lojaperfil)
        return qs

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        user = self.request.user
        if not user.is_authenticated or not user.loja:
            # Serializer somente leitura
            class ProdutoLeituraSerializer(serializers.ModelSerializer):
                loja = serializers.StringRelatedField()

                class Meta:
                    model = Produto
                    fields = ["id", "nome", "descricao", "preco", "disponivel", "loja"]
                    read_only_fields = fields

            return ProdutoLeituraSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "lojaperfil"):
            raise PermissionDenied("Apenas perfis de loja podem adicionar produtos.")
        serializer.save(loja=user.lojaperfil)

    def perform_destroy(self, instance):
        user = self.request.user
        if not hasattr(user, "lojaperfil") or instance.loja != user.lojaperfil:
            raise PermissionDenied("Você não tem permissão para excluir este produto.")
        instance.delete()


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
