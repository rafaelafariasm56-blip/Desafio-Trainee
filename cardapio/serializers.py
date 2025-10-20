from rest_framework import serializers
from .models import Prato, Oferta

class OfertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oferta
        fields = ["id", "prato", "data", "quantidade_disponivel", "preco", "ativa"]
        read_only_fields = ["prato"]

class PratoSerializer(serializers.ModelSerializer):
    ofertas = OfertaSerializer(many=True, read_only=True)
    loja = serializers.ReadOnlyField(source="loja.username")

    class Meta:
        model = Prato
        fields = ["id", "nome", "descricao", "imagem", "loja", "criado_em", "ofertas"]
