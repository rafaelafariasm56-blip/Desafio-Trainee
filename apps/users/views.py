from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from apps.users.models import User, Pagamento
from apps.users.serializers import UserRegisterSerializer, UserSerializer, PagamentoSerializer, LoginSerializer
from rest_framework.reverse import reverse
from rest_framework.views import APIView


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email"]

    # 🔹 Registro
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        url_path="register",
        url_name="register"
    )
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Usuário registrado com sucesso!",
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)

    # 🔹 Login
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        url_path="login",
        url_name="login",
        serializer_class=LoginSerializer
    )
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )
        if not user:
            return Response({"detail": "Credenciais inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login realizado com sucesso!",
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }
        }, status=status.HTTP_200_OK)

class PagamentoMetodoViewSet(viewsets.ModelViewSet):
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pagamento.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class ApiRootView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Retorna endpoints diferentes para:
        - Usuários não autenticados
        - Lojas autenticadas
        - Clientes autenticados
        """
        base = {}

        # Sempre visível
        base["register"] = reverse("users-registrar", request=request)
        base["login"] = reverse("users-login", request=request)

        user = request.user
        if not user.is_authenticated:
            return Response(base)

        # Se for loja
        if user.loja:
            base["cardapio"] = reverse("cardapio-list", request=request)
            base["pedidos_em_andamento"] = reverse("pedidos-list", request=request)
        else:
            # Se for cliente final
            base["area_de_vendas"] = reverse("produtos-list", request=request)
            base["buscar_por_loja"] = reverse("lojas-list", request=request)
            base["metodos_de_pagamento"] = reverse("payments-list", request=request)
            base["historico_de_pedidos"] = reverse("pedidos-list", request=request)

        return Response(base)