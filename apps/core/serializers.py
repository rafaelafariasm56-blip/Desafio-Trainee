from rest_framework import serializers
from apps.core.models import LojaPerfil, Produto, Cardapio
from datetime import datetime

class ProdutoSerializer(serializers.ModelSerializer):
    loja = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Produto
        fields = ['id', 'nome', 'descricao', 'slug', 'active', 'criada_em', 'loja']


class CardapioSerializer(serializers.ModelSerializer):
    produtos = ProdutoSerializer(many=True, read_only=True)

    class Meta:
        model = Cardapio
        fields = ['id', 'loja', 'produtos']
        read_only_fields = ['loja']

class LojaSerializer(serializers.ModelSerializer):
    produtos = ProdutoSerializer(many=True, read_only=True)
    cardapios = CardapioSerializer(many=True, read_only=True)

    class Meta:
        model = LojaPerfil
        fields = ['id', 'nome', 'endereco', 'aberta', 'produtos', 'cardapios']
