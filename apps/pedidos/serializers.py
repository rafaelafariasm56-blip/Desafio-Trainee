from rest_framework import serializers
from .models import Carrinho, Pedido, PedidoItem, Produto
from apps.users.models import Pagamento
from apps.pedidos.models import CarrinhoItem
from apps.core.serializers import ProdutoSerializer

class CarrinhoItemSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer(read_only=True)
    produto_id = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.all(), source="produto", write_only=True
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CarrinhoItem
        fields = ["id", "produto", "produto_id", "quantidade", "data", "subtotal"]

    def get_subtotal(self, obj):
        return obj.subtotal


class CarrinhoSerializer(serializers.ModelSerializer):
    items = CarrinhoItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Carrinho
        fields = ["id", "user", "criado_em", "items", "total"]
        read_only_fields = ["user", "criado_em", "total"]

class PedidoItemSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)

    class Meta:
        model = PedidoItem
        fields = ['id', 'produto', 'produto_nome', 'quantidade', 'preco', 'data']
        read_only_fields = ['id', 'preco', 'produto_nome']

class PedidoSerializer(serializers.ModelSerializer):
    itens = PedidoItemSerializer(many=True, write_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'user', 'loja', 'loja_nome', 'criado_em', 'status',
            'total', 'metodo_pagamento', 'code', 'itens'
        ]
        read_only_fields = ['id', 'user', 'criado_em', 'total', 'status', 'code', 'loja']

    def create(self, validated_data):
        itens_data = validated_data.pop('itens')
        user = self.context['request'].user

        if user.loja:
            raise serializers.ValidationError("Lojas não podem criar pedidos.")

        primeiro_produto = Produto.objects.get(id=itens_data[0]['produto'].id)
        loja = primeiro_produto.loja

        pedido = Pedido.objects.create(user=user, loja=loja, **validated_data)

        total = 0
        for item_data in itens_data:
            produto = item_data['produto']
            quantidade = item_data.get('quantidade', 1)
            preco_unitario = produto.preco

            PedidoItem.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=quantidade,
                preco=preco_unitario
            )
            total += quantidade * preco_unitario

        pedido.total = total
        pedido.save()
        return pedido
    
class PedidoHistoricoSerializer(serializers.ModelSerializer):
    items = PedidoItemSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'criado_em', 'items', 'total']
        read_only_fields = fields

class FinalizarCompraSerializer(serializers.Serializer):
    metodo_pagamento_id = serializers.IntegerField()

    def create(self, validated_data):
        user = self.context["request"].user
        metodo_pagamento = Pagamento.objects.get(id=validated_data["metodo_pagamento_id"], user=user)
        carrinho = Carrinho.objects.get(user=user)

        if not carrinho.items.exists():
            raise serializers.ValidationError("Seu carrinho está vazio.")

        total = sum(item.produto.preco * item.quantidade for item in carrinho.items.all())

        pedido = Pedido.objects.create(
            user=user,
            loja=carrinho.items.first().produto.loja,
            metodo_pagamento=metodo_pagamento,
            total=total,
        )

        for item in carrinho.items.all():
            PedidoItem.objects.create(
                pedido=pedido,
                produto=item.produto,
                quantidade=item.quantidade,
                preco=item.produto.preco,
                data=item.data,
            )

        carrinho.items.all().delete()
        return pedido