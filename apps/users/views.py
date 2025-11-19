from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.contrib.auth import authenticate
from apps.users.models import User
from apps.users.serializers import UserRegisterSerializer, UserSerializer, LoginSerializer, CustomTokenObtainPairSerializer
from apps.users.permissions import IsDonoeReadOnly
from apps.core.models import LojaPerfil
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(tags=["Autenticação"])
class ApiRootView(APIView):
    """
    Redireciona automaticamente para o painel correto, dependendo do tipo de usuário.
    """
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=["Autenticação"],
        operation_summary="Redireciona se autenticado",
        operation_description="Se o usuário estiver logado, redireciona para o painel correto. Caso contrário, retorna links de login e registro.",
        responses={
            200: openapi.Response(
                description="Links de login e registro para usuários não autenticados",
                examples={"application/json": {
                    "register": "http://127.0.0.1:8000/api/users/register/",
                    "login": "http://127.0.0.1:8000/api/users/login/"
                }}
            )
        }
    )
    def get(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, "lojaperfil"):
                return redirect("painel-loja")
            return redirect("painel-usuario")
        return Response({
            "register": reverse("users:register", request=request),
            "login": reverse("users:login", request=request),
        })

@swagger_auto_schema(tags=["Autenticação"])
class LoginView(APIView):
    """
    Autentica o usuário usando username e password.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  

    @swagger_auto_schema(
        tags=["Autenticação"],
        operation_summary="Realiza login",
        operation_description=(
            "Autentica o usuário e retorna cookies JWT, além de redirecionar "
            "para o painel correto com base nas permissões."
        ),
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login realizado com sucesso",
                examples={"application/json": {"message": "Login realizado com sucesso"}}
            ),
            401: openapi.Response(
                description="Credenciais inválidas",
                examples={"application/json": {"detail": "Credenciais inválidas"}}
            )
        }
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Credenciais inválidas"}, status=401)

        refresh = CustomTokenObtainPairSerializer.get_token(user)
        access = refresh.access_token

        is_loja = access.payload.get("is_loja", False)

        redirect_url = reverse(
            "painel-loja" if is_loja else "painel-usuario",
            request=request
        )

        response = redirect(redirect_url)

        response.set_cookie(
            "access_token",
            str(access),
            httponly=True,
            samesite="Lax",
            path="/"
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            samesite="Lax",
            path="/"
        )

        return response


@swagger_auto_schema(tags=["Autenticação"])
class LogoutView(APIView):
    """
    Realiza logout removendo cookies JWT.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Autenticação"],
        operation_summary="Logout do usuário",
        operation_description="Remove os cookies JWT do navegador.",
        responses={200: "Logout realizado com sucesso"}
    )
    def post(self, request):
        response = Response({"detail": "Logout realizado com sucesso."})
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response

class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuários.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "nome"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsDonoeReadOnly()]
        elif self.action == "register":
            return [AllowAny()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == "register":
            return UserRegisterSerializer
        return UserSerializer

    @swagger_auto_schema(
        tags=["Usuários"],
        operation_summary="Registrar novo usuário",
        request_body=UserRegisterSerializer,
        responses={201: UserSerializer, 400: "Dados inválidos"}
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if hasattr(user, "loja"):
            LojaPerfil.objects.get_or_create(user=user, nome=user.username)
        return Response({
            "message": "Usuário registrado com sucesso!",
            "user": UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(tags=["Painel do Usuário"])
class PainelUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Painel do Usuário"],
        operation_summary="Painel do usuário final",
        operation_description="Retorna os links disponíveis para o usuário final.",
        responses={200: openapi.Response(
            description="Endpoints disponíveis",
            examples={"application/json": {
                "painel_usuario": {
                    "area_de_vendas": "/api/produtos/",
                    "metodo_de_pagamento": "/api/pedidos/pagamento/",
                    "pedidos": "/api/pedidos/historico-pedidos/",
                    "endereço": "/api/pedidos/endereco/",
                    "carrinho": "/api/pedidos/carrinho/",
                    "finalizar pagamento": "/api/pedidos/pagamento/pagar/"
                }
            }}
        )}
    )
    def get(self, request):
        claims = request.auth or {}
        if claims.get("is_loja"):
            return Response({"detail": "Usuário é loja. Use /painel/loja/"}, status=403)
        painel = {
            "area_de_vendas": reverse("produtos-list", request=request),
            "metodo_de_pagamento": reverse("pedidos:pagamento-list", request=request),
            "pedidos": reverse("pedidos:historico-pedidos-list", request=request),
            "endereço": reverse("pedidos:endereco-list", request=request),
            "carrinho": reverse("pedidos:carrinho-list", request=request),
            "finalizar pagamento": reverse("pedidos:pagamento-pagar", request=request),
        }
        return Response({"painel_usuario": painel})

@swagger_auto_schema(tags=["Painel da Loja"])
class PainelLojaView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Painel da Loja"],
        operation_summary="Painel da loja",
        operation_description="Retorna os links disponíveis para uma loja.",
        responses={200: openapi.Response(
            description="Endpoints disponíveis",
            examples={"application/json": {
                "painel_loja": {
                    "meu_cardapio": "/api/produtos/",
                    "historico_de_pedidos": "/api/pedidos/historico-loja/",
                    "faturamento": "/api/pedidos/faturamento-periodo/"
                }
            }}
        )}
    )
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




