from rest_framework import viewsets, permissions, filters, serializers
from django_filters.rest_framework import DjangoFilterBackend
from .models import Prato, Oferta
from .serializers import PratoSerializer, OfertaSerializer
from users.permissions import EhLoja

class PratoViewSet(viewsets.ModelViewSet):
    queryset = Prato.objects.all().order_by("-criado_em")
    serializer_class = PratoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "descricao"]
    ordering_fields = ["criado_em", "nome"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "minhas_lojas"]:
            return [permissions.IsAuthenticated(), EhLoja()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(loja=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == "LOJA":
            return Prato.objects.filter(loja=user)
        return super().get_queryset()


class OfertaViewSet(viewsets.ModelViewSet):
    queryset = Oferta.objects.select_related("prato").all()
    serializer_class = OfertaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["data", "ativa", "prato__loja"]
    ordering_fields = ["data", "preco"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), EhLoja()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        prato = serializer.validated_data.get("prato")
        if prato.loja != self.request.user:
            raise serializers.ValidationError("Este prato não pertence à sua loja.")
        serializer.save()
