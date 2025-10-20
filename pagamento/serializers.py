from rest_framework import serializers
from .models import FormaPagamento

class FormaPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPagamento
        fields = ["id", "cliente", "nome", "detalhes"]
        read_only_fields = ["cliente"]
