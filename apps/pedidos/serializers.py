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
        if obj.tipo == "cartao":
            return f"{obj.bandeira} ****{obj.numero[-4:]}"
        return obj.apelido or "Método de Pagamento"



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
            metodo_pagamento = Pagamento.objects.get(id=validated_data["metodo_pagamento_id"], user=user)
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
            loja = itens[0].produto.loja
            total = sum(item.produto.preco * item.quantidade for item in itens)

            pedido = Pedido.objects.create(
                user=user,
                loja=loja,
                total=total,
                metodo_pagamento=metodo_pagamento
            )

            pedidos_criados.append(pedido)

        carrinho.items.all().delete()

        return pedidos_criados



class AtualizarStatusPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = ['status']
        read_only_fields = []

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
            "metodo_pagamento"]  

    def validate_status(self, value):
        if value not in dict(Pedido.STATUS_CHOICES):
            raise serializers.ValidationError("Status inválido.")
        return value
    
class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = ["id","metodo","nome_no_cartao","numero_cartao", "validade","cvv","chave_pix","observacao","ativo",]

    def validate(self, attrs):
        metodo = attrs.get("metodo")

        if metodo == "cartao":
            required_fields = ["nome_no_cartao", "numero_cartao", "validade", "cvv"]

            for field in required_fields:
                value = attrs.get(field)
                if not value:
                    raise serializers.ValidationError(
                        {field: f"O campo '{field}' é obrigatório para pagamento com cartão."}
                    )

        if metodo == "outro":
            if not attrs.get("observacao"):
                raise serializers.ValidationError(
                    {"observacao": "A observação é obrigatória quando o método é 'outro'."}
                )

        return attrs    