from rest_framework import serializers
from .models import Carrinho, CarrinhoItem, Pedido, PedidoItem
from apps.core.serializers import ProdutoSerializer
import uuid

class CarrinhoItemSerializer(serializers.ModelSerializer):
    produto = serializers.PrimaryKeyRelatedField(read_only=False, queryset=CarrinhoItem._meta.get_field("produto").related_model.objects.all())

    class Meta:
        model = CarrinhoItem
        fields = "__all__"
        read_only_fields = ("carrinho",)

class CarrinhoSerializer(serializers.ModelSerializer):
    items = CarrinhoItemSerializer(many=True, read_only=True)

    class Meta:
        model = Carrinho
        fields = ("id", "user", "items")

class PedidoItemSerializer(serializers.ModelSerializer):
    product = ProdutoSerializer(read_only=True)

    class Meta:
        model = PedidoItem
        fields = "__all__"
        read_only_fields = ("order",)

class PedidoSerializer(serializers.ModelSerializer):
    items = CarrinhoItemSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = "__all__"
        read_only_fields = ("code", "criado_em", "status", "total", "loja")

    def generate_code(self):
        return uuid.uuid4().hex[:12].upper()
