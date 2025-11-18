from rest_framework import serializers
from .models import LojaPerfil, Produto, Cardapio



class ProdutoSerializer(serializers.ModelSerializer):
    loja = serializers.StringRelatedField(read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Produto
        fields = [
            "id", "nome", "descricao", "preco", "quantidade",
            "disponivel", "criada_em", "atualizada_em",
            "loja", "loja_nome"
        ]
        read_only_fields = [
            "id", "loja", "loja_nome", "criada_em", "atualizada_em"
        ]

    def validate(self, attrs):
        request = self.context["request"]
        claims = request.auth  

        if not claims:
            raise serializers.ValidationError("Token inválido ou ausente.")

        if not claims.get("is_loja"):
            raise serializers.ValidationError("Apenas lojas podem criar produtos.")

        if not claims.get("loja_id"):
            raise serializers.ValidationError("Loja não encontrada no token.")

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        claims = request.auth

        loja_id = claims.get("loja_id")

        try:
            loja = LojaPerfil.objects.get(id=loja_id)
        except LojaPerfil.DoesNotExist:
            raise serializers.ValidationError("Loja associada ao token não existe.")

        validated_data["loja"] = loja
        return super().create(validated_data)

class ProdutoLeituraSerializer(serializers.ModelSerializer):
    loja = serializers.StringRelatedField()
    loja_nome = serializers.CharField(source="loja.nome", read_only=True)

    class Meta:
        model = Produto
        fields = [
            "id",
            "nome",
            "descricao",
            "preco",
            "quantidade",
            "disponivel",
            "criada_em",
            "atualizada_em",
            "loja",
            "loja_nome",
        ]
        read_only_fields = fields
        
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
