from rest_framework import serializers
from .models import Carrinho, Pedido, PedidoItem, Produto
from apps.users.models import Pagamento
from apps.pedidos.models import CarrinhoItem
from apps.core.serializers import ProdutoSerializer


class CarrinhoAdicionarItemSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1, default=1)


class CarrinhoItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CarrinhoItem
        fields = ["id", "produto", "quantidade", "subtotal"]
        extra_kwargs = {
            "produto": {"write_only": True},
        }


class CarrinhoSerializer(serializers.ModelSerializer):
    items = CarrinhoItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Carrinho
        fields = ["id", "items", "total"]



class MetodoPagamentoSerializer(serializers.ModelSerializer):
    descricao = serializers.SerializerMethodField()

    class Meta:
        model = Pagamento
        fields = ["id", "metodo", "descricao"]

    def get_descricao(self, obj):
        return str(obj)


class MetodoPagamentoListaSerializer(serializers.ModelSerializer):
    nome_exibicao = serializers.SerializerMethodField()

    class Meta:
        model = Pagamento
        fields = ["nome_exibicao"]

    def get_nome_exibicao(self, obj):
        if obj.metodo == "cartao":
            return f"Cartão ****{obj.numero_cartao[-4:]}"
        return obj.observacao or "Método de pagamento"


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = "__all__"

    def validate_metodo_pagamento(self, value):
        user = self.context["request"].user
        if value.user != user:
            raise serializers.ValidationError("Método de pagamento inválido.")
        return value



class FinalizarPagamentoSerializer(serializers.Serializer):
    metodo_pagamento_id = serializers.IntegerField()

    def create(self, validated_data):
        user = self.context["request"].user

        try:
            metodo_pagamento = Pagamento.objects.get(
                id=validated_data["metodo_pagamento_id"],
                user=user
            )
        except Pagamento.DoesNotExist:
            raise serializers.ValidationError("Método de pagamento inválido.")

        try:
            carrinho = Carrinho.objects.get(user=user)
        except Carrinho.DoesNotExist:
            raise serializers.ValidationError("Carrinho não encontrado.")

        if not carrinho.items.exists():
            raise serializers.ValidationError("Seu carrinho está vazio.")

        pedidos_criados = []

        lojas = {}
        for item in carrinho.items.all():
            loja = item.produto.loja

            if loja.id not in lojas:
                lojas[loja.id] = []

            lojas[loja.id].append(item)

        for loja_id, itens in lojas.items():
            for item in itens:
                produto = item.produto
                if item.quantidade > produto.quantidade:
                    raise serializers.ValidationError(
                        f"Estoque insuficiente para '{produto.nome}'. Disponível: {produto.quantidade}."
                    )

        for loja_id, itens in lojas.items():
            loja = itens[0].produto.loja
            total = sum(item.produto.preco * item.quantidade for item in itens)

            pedido = Pedido.objects.create(
                user=user,
                loja=loja,
                total=total,
                metodo_pagamento=metodo_pagamento
            )

            for item in itens:
                produto = item.produto

                PedidoItem.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=item.quantidade,
                    preco=produto.preco  
                )

                produto.quantidade -= item.quantidade
                if produto.quantidade <= 0:
                    produto.quantidade = 0
                    produto.disponivel = False
                produto.save()

            pedidos_criados.append(pedido)

        # Limpar carrinho
        carrinho.items.all().delete()

        return pedidos_criados



class AtualizarStatusPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = ['status']

    def validate_status(self, value):
        if value not in dict(Pedido.STATUS_CHOICES):
            raise serializers.ValidationError("Status inválido.")
        return value


class PedidoLojaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = [
            "id",
            "criado_em",
            "status",
            "total",
            "code",
            "user",
            "loja",
            "metodo_pagamento"
        ]
        read_only_fields = [
            "id",
            "criado_em",
            "total",
            "code",
            "user",
            "loja",
            "metodo_pagamento"
        ]

class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = [
            "id",
            "metodo",
            "nome_no_cartao",
            "numero_cartao",
            "validade",
            "cvv",
            "chave_pix",
            "observacao",
            "ativo",
        ]

    def validate(self, attrs):
        metodo = attrs.get("metodo")

        if metodo == "cartao":
            for campo in ["nome_no_cartao", "numero_cartao", "validade", "cvv"]:
                if not attrs.get(campo):
                    raise serializers.ValidationError(
                        {campo: f"O campo '{campo}' é obrigatório para cartão."}
                    )

        if metodo == "pix" and not attrs.get("chave_pix"):
            raise serializers.ValidationError(
                {"chave_pix": "A chave PIX é obrigatória para pagamento via PIX."}
            )

        if metodo == "outro" and not attrs.get("observacao"):
            raise serializers.ValidationError(
                {"observacao": "A observação é obrigatória quando o método é 'outro'."}
            )

        return attrs

class FaturamentoFiltroSerializer(serializers.Serializer):
    data_inicial = serializers.DateField(required=True)
    data_final = serializers.DateField(required=True)