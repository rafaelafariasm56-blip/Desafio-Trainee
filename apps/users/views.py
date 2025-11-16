from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from apps.users.models import User
from apps.users.serializers import UserRegisterSerializer, UserSerializer, LoginSerializer, CustomTokenObtainPairSerializer
from apps.users.permissions import IsDonoeReadOnly
from apps.core.models import LojaPerfil


class ApiRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            claims = request.auth or {}
            if claims.get("loja"):
                return redirect("painel-loja")
            return redirect("painel-usuario")

        return Response({
            "login": reverse("users:login", request=request),
            "register": reverse("users:register", request=request),
        })



class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Credenciais inválidas"}, status=401)

        refresh = CustomTokenObtainPairSerializer.get_token(user)
        access = refresh.access_token

        claims = access.payload

        is_loja = claims.get("is_loja", False)

        redirect_url = reverse(
            "painel-loja" if is_loja else "painel-usuario", 
            request=request
        )

        response = redirect(redirect_url)

        response.set_cookie("access_token", str(access), httponly=True, path="/")
        response.set_cookie("refresh_token", str(refresh), httponly=True, path="/")

        return response



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"detail": "Logout realizado com sucesso."})

        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")

        return response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "nome"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsDonoeReadOnly()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == "register":
            return UserRegisterSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        claims = self.request.auth or {}

        if not user.is_authenticated:
            return User.objects.none()

        is_loja = claims.get("is_loja", False)
        loja_id = claims.get("loja_id")

        if is_loja:
            return User.objects.filter(id=user.id)

        return User.objects.filter(id=user.id)


    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="register")
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.loja:
            LojaPerfil.objects.get_or_create(user=user, nome=user.username)

        return Response({
            "message": "Usuário registrado com sucesso!",
            "user": UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class PainelUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        claims = request.auth or {}

        if claims.get("is_loja"):
            return Response(
                {"detail": "Usuário é loja. Use /painel/loja/"},
                status=403
            )

        painel = {
            "area_de_vendas": reverse("produtos-list", request=request),
            "buscar_por_loja": reverse("produtos-list", request=request),
            "metodo_de_pagamento": reverse("pedidos:pagamento-list", request=request),
            "historico_de_pedidos": reverse("pedidos:historico-pedidos-list", request=request),
            "carrinho": reverse("pedidos:carrinho-list", request=request),
            "finalizar_pagamento": reverse("pedidos:pagamento-pagar", request=request),
        }

        return Response({"painel_usuario": painel})



class PainelLojaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        claims = request.auth or {}

        if not claims.get("is_loja"):
            return Response({"detail": "Apenas lojas podem acessar."}, status=403)

        painel = {
            "meu_cardapio": reverse("produtos-list", request=request),
            "historico_de_pedidos": reverse("pedidos:historico-loja-list", request=request),
            "faturamento": reverse("pedidos:faturamento-periodo", request=request),
        }

        return Response({"painel_loja": painel})




