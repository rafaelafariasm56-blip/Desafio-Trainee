from rest_framework import viewsets, permissions, filters, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.users.models import User
from apps.core.models import Produto, LojaPerfil, Cardapio
from apps.users.serializers import UserSerializer, UserRegisterSerializer, LoginSerializer
from apps.users.permissions import IsDonoeReadOnly
from apps.core.serializers import ProdutoSerializer, LojaSerializer, CardapioSerializer
from rest_framework.reverse import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.filter(active=True)
    serializer_class = ProdutoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'descricao', 'loja__nome']
    ordering_fields = ['criada_em', 'nome', 'preco']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user

        if not user.loja:
            raise PermissionDenied("Apenas perfis de loja podem adicionar produtos.")

        try:
            loja = LojaPerfil.objects.get(user=user)
        except LojaPerfil.DoesNotExist:
            raise PermissionDenied("Perfil de loja não encontrado. Crie um perfil antes de adicionar produtos.")

        serializer.save(loja=loja)

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
    serializer_class = ProdutoSerializer
    queryset = Produto.objects.all()
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.loja and hasattr(user, "lojaperfil"):
            return Produto.objects.filter(loja=user.lojaperfil)
        return Produto.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.loja:
            raise PermissionDenied("Apenas perfis de loja podem adicionar produtos.")

        try:
            loja = LojaPerfil.objects.get(user=user)
        except LojaPerfil.DoesNotExist:
            raise PermissionDenied("Perfil de loja não encontrado.")

        serializer.save(loja=loja)