from rest_framework import serializers
from .models import LojaPerfil, Produto, Cardapio



class ProdutoSerializer(serializers.ModelSerializer):
    loja = serializers.StringRelatedField(read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    preco = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Produto
        fields = ["id","nome","descricao","preco","quantidade","disponivel","criada_em","atualizada_em","loja","loja_nome"]
        read_only_fields = ["id", "loja", "loja_nome", "criada_em", "atualizada_em"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None

        if not user or not user.loja:
            raise serializers.ValidationError("Apenas perfis de loja podem criar produtos.")

        try:
            loja = LojaPerfil.objects.get(user=user)
        except LojaPerfil.DoesNotExist:
            raise serializers.ValidationError("Perfil de loja não encontrado.")

        validated_data["loja"] = loja
        return super().create(validated_data)

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
