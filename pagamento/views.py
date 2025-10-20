from rest_framework import viewsets, permissions
from .models import FormaPagamento
from .serializers import FormaPagamentoSerializer
from users.permissions import EhCliente

class FormaPagamentoViewSet(viewsets.ModelViewSet):
    serializer_class = FormaPagamentoSerializer
    permission_classes = [permissions.IsAuthenticated, EhCliente]

    def get_queryset(self):
        return FormaPagamento.objects.filter(cliente=self.request.user)

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user)
