from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.models import Produto, Disponibilidade, LojaPerfil
from .serializers import ProdutoSerializer, DisponibilidadeSerializer, PerfilLojaSerializer
from apps.users.permissions import IsLoja

class ProdutoViewset(viewsets.ModelViewSet):
    queryset = Produto.objects.all().select_related("establishment")
    serializer_class = ProdutoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["loja_id", "active"]
    search_fields = ["nome", "descricao", "loja_nome"]
    ordering_fields = ["criada_em", "nome"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "create_availability"]:
            return [IsAuthenticated(), IsLoja()]
        return [AllowAny()]

    def perform_create(self, serializer):
        est = LojaPerfil.objects.get(user=self.request.user)
        serializer.save(establishment=est)

    @action(detail=True, methods=["post"], url_path="availability")
    def create_availability(self, request, pk=None):
        product = self.get_object()
        if product.establishment.user != request.user:
            return Response({"detail": "Not allowed"}, status=403)

        data = request.data.copy()
        data["produto"] = product.id
        serializer = ProductAvailabilitySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

class PerfilLojaViewset(viewsets.ModelViewSet):
    queryset = LojaPerfil.objects.all()
    serializer_class = PerfilLojaSerializer
    permission_classes = [IsAuthenticated, IsLoja]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
