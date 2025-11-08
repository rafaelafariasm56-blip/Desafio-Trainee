from rest_framework import viewsets, status, filters, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.reverse import reverse
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from apps.users.models import User, Pagamento
from apps.users.serializers import UserRegisterSerializer, UserSerializer, PagamentoSerializer, LoginSerializer
from apps.users.permissions import IsDonoeReadOnly
from apps.core.models import LojaPerfil, Produto
from apps.core.serializers import ProdutoSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "nome"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsDonoeReadOnly()]
        return [AllowAny()]

    def get_serializer_class(self):
        match self.action:
            case "create": return UserRegisterSerializer
            case "login": return LoginSerializer
            case _: return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        return User.objects.filter(loja=not user.loja)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.loja:
            LojaPerfil.objects.get_or_create(user=user, nome=user.username)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Usuário registrado com sucesso!",
            "user": UserSerializer(user).data,
            "tokens": {"refresh": str(refresh), "access": str(refresh.access_token)}
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
            return Response({"detail": "Credenciais inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        LojaPerfil.objects.get_or_create(user=user, nome=user.username) if user.loja else None

        painel = (
            {
                "meu_cardapio": reverse("cardapio-list", request=request),
                "meus_produtos": reverse("produtos-list", request=request),
                "historico_de_pedidos": reverse("historico-loja-list", request=request),
                "meus_pedidos": reverse("meus_pedidos-list", request=request),
            } if user.loja else {
                "area_de_vendas": reverse("produtos-list", request=request),
                "buscar_por_loja": reverse("lojas-list", request=request),
                "metodo_de_pagamento": reverse("pagamentos-list", request=request),
                "historico_de_pedidos": reverse("historico-pedidos-list", request=request),
                "carrinho": reverse("carrinho-list", request=request),
            }
        )

        painel_url = reverse("painel-loja", request=request) if user.loja else reverse("painel-usuario", request=request)
        return Response({
            "message": f"Login realizado com sucesso! Bem-vindo(a), {user.username}",
            "user": UserSerializer(user).data,
            "tokens": {"refresh": str(refresh), "access": str(refresh.access_token)},
            "painel": painel,
            "painel_url": painel_url,
        })
    
class PainelUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        painel = {
            "area_de_vendas": reverse("produtos-list", request=request),
            "buscar_por_loja": reverse("lojas-list", request=request),
            "metodo_de_pagamento": reverse("pagamentos-list", request=request),
            "historico_de_pedidos": reverse("pedidos:historico-pedidos-list", request=request),
            "carrinho": reverse("pedidos:carrinho-list", request=request),
        }
        return Response({"painel_usuario": painel})


class PainelLojaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        painel = {
            "meu_cardapio": reverse("cardapio-list", request=request),
            "meus_produtos": reverse("produtos-list", request=request),
            "historico_de_pedidos": reverse("pedidos:historico-loja-list", request=request),
            "meus_pedidos": reverse("pedidos:meus-pedidos-list", request=request),
        }
        return Response({"painel_loja": painel})