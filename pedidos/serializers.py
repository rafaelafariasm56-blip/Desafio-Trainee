from rest_framework import serializers
from .models import Pedido, ItemPedido
from cardapio.models import Oferta
from decimal import Decimal
from django.db import transaction

class ItemPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPedido
        fields = ["oferta", "quantidade", "preco"]


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True)

    class Meta:
        model = Pedido
        fields = ["id", "codigo", "cliente", "loja", "criado_em", "status", "total", "itens"]
        read_only_fields = ["codigo", "criado_em", "total", "cliente", "loja"]

    def validate(self, data):
        itens = data.get("itens", [])
        if not itens:
            raise serializers.ValidationError("O pedido precisa ter itens.")
        lojas = set([item["oferta"].prato.loja_id for item in itens])
        if len(lojas) > 1:
            raise serializers.ValidationError("Todos os itens devem ser da mesma loja.")
        return data

    @transaction.atomic
    def create(self, validated_data):
        itens_data = validated_data.pop("itens")
        user = self.context["request"].user
        loja = itens_data[0]["oferta"].prato.loja
        pedido = Pedido.objects.create(cliente=user, loja=loja)

        total = Decimal("0")
        for item in itens_data:
            oferta = item["oferta"]
            qtd = item["quantidade"]
            preco = oferta.preco
            ItemPedido.objects.create(pedido=pedido, oferta=oferta, quantidade=qtd, preco=preco)
            oferta.quantidade_disponivel -= qtd
            oferta.save()
            total += preco * qtd
        pedido.total = total
        pedido.save()
        return pedido
