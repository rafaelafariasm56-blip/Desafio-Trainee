from rest_framework import serializers
from apps.core.models import LojaPerfil, Produto, Cardapio, CardapioItem
from datetime import datetime

class ProdutoSerializer(serializers.ModelSerializer):
    loja = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Produto
        fields = ['id', 'nome', 'descricao', 'slug', 'active', 'criada_em', 'loja']


class CardapioItemSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer(read_only=True)
    produto_id = serializers.PrimaryKeyRelatedField(queryset=Produto.objects.all(), source="produto", write_only=True)

    class Meta:
        model = CardapioItem
        fields = ['id', 'produto', 'produto_id', 'preco', 'estoque', 'disponivel', 'dias_disponiveis']


class CardapioSerializer(serializers.ModelSerializer):
    itens = CardapioItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cardapio
        fields = ['id', 'nome', 'data_criacao', 'loja', 'itens']
        read_only_fields = ['loja', 'data_criacao']


class LojaSerializer(serializers.ModelSerializer):
    produtos = ProdutoSerializer(many=True, read_only=True)
    cardapios = CardapioSerializer(many=True, read_only=True)

    class Meta:
        model = LojaPerfil
        fields = ['id', 'nome', 'endereco', 'aberta', 'produtos', 'cardapios']
