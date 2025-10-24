from rest_framework import serializers
from .models import LojaPerfil, Produto, Disponibilidade

class PerfilLojaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LojaPerfil
        fields = "__all__"
        read_only_fields = ("user",)

class DisponibilidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilidade
        fields = "__all__"

class ProdutoSerializer(serializers.ModelSerializer):
    disponibilidade = DisponibilidadeSerializer(many=True, read_only=True)
    loja = PerfilLojaSerializer(read_only=True)

    class Meta:
        model = Produto
        fields = "__all__"
        read_only_fields = ("loja", "criada_em")
