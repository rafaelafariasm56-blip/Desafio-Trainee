from rest_framework import serializers
from apps.core.models import LojaPerfil, Produto, Cardapio


class ProdutoSerializer(serializers.ModelSerializer):
    loja = serializers.StringRelatedField(read_only=True)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Produto
        fields = ["id", "nome", "descricao", "preco", "active", "criada_em", "loja"]
        read_only_fields = ["criada_em", "loja"]


class CardapioSerializer(serializers.ModelSerializer):
    produtos = ProdutoSerializer(many=True, read_only=True)

    class Meta:
        model = Cardapio
        fields = ["id", "loja", "produtos"]
        read_only_fields = ["loja"]


class LojaSerializer(serializers.ModelSerializer):
    produtos = ProdutoSerializer(many=True, read_only=True, source="produto_set")
    cardapio = CardapioSerializer(read_only=True)

    class Meta:
        model = LojaPerfil
        fields = ["id", "nome", "endereco", "aberta", "produtos", "cardapio"]
