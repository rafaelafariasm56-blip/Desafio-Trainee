from rest_framework import viewsets, status, permissions, filters, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from apps.users.models import User, Pagamento
from apps.users.serializers import UserRegisterSerializer, UserSerializer, PagamentoSerializer, LoginSerializer
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from apps.users.permissions import IsDonoeReadOnly
from apps.core.models import LojaPerfil, Produto
from apps.core.serializers import ProdutoSerializer
from rest_framework.exceptions import PermissionDenied


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "nome"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsDonoeReadOnly]
        else:
            permission_classes = [AllowAny]
        return [perm() for perm in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegisterSerializer
        elif self.action == "login":
            return LoginSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if user.loja:
            return User.objects.filter(loja=False)
        return User.objects.filter(loja=True)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        """Registro de usuário (cliente ou loja) com token automático"""
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.loja:
            LojaPerfil.objects.get_or_create(user=user, nome=user.username)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Usuário registrado com sucesso!",
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )
        if not user:
            return Response({"detail": "Credenciais inválidas."},
                            status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        if user.loja:
            LojaPerfil.objects.get_or_create(user=user, nome=user.username)

        if user.loja:
            painel = {
                "meu_cardapio": reverse("cardapio-list", request=request),
                "meus_produtos": reverse("produtos-list", request=request),
                "historico_de_pedidos": reverse("historico-loja-list", request=request),
            }
        else:
            painel = {
                "area_de_vendas": reverse("produtos-list", request=request),
                "buscar_por_loja": reverse("lojas-list", request=request),
                "metodo_de_pagamento": reverse("pagamentos-list", request=request),
                "historico_de_pedidos": reverse("historico-pedidos-list", request=request),
                "carrinho": reverse("carrinho-list", request=request),

            }

        return Response({
            "message": f"Login realizado com sucesso! Bem-vindo(a), {user.username}",
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "painel": painel
        }, status=status.HTTP_200_OK)

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
    
class PagamentoListCreateView(generics.ListCreateAPIView):
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pagamento.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PagamentoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pagamento.objects.filter(user=self.request.user)
