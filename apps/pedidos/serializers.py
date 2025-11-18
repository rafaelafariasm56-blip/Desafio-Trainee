from rest_framework import serializers
from .models import Carrinho, Pedido, PedidoItem, Produto
from apps.users.models import Pagamento, Endereco
from apps.pedidos.models import CarrinhoItem


class CarrinhoAdicionarItemSerializer(serializers.Serializer):
    produto = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.all()
    )
    quantidade = serializers.IntegerField(min_value=1, default=1)


class CarrinhoRemoverItemSerializer(serializers.Serializer):
    produto = serializers.PrimaryKeyRelatedField(queryset=Produto.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if not request:
            return

        user = request.user
        carrinho, _ = Carrinho.objects.get_or_create(user=user)

        self.fields["produto"].queryset = Produto.objects.filter(
            carrinhoitem__carrinho=carrinho
        )

class CarrinhoAlterarQuantidadeSerializer(serializers.Serializer):
    produto = serializers.PrimaryKeyRelatedField(queryset=Produto.objects.none())
    quantidade = serializers.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if not request:
            return

        user = request.user
        carrinho, _ = Carrinho.objects.get_or_create(user=user)

        self.fields["produto"].queryset = Produto.objects.filter(
            carrinhoitem__carrinho=carrinho
        )


class CarrinhoItemSerializer(serializers.ModelSerializer):
    produto_id = serializers.IntegerField(source="produto.id", read_only=True)
    produto_nome = serializers.CharField(source="produto.nome", read_only=True)
    produto_preco = serializers.DecimalField(
        source="produto.preco",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CarrinhoItem
        fields = [
            "id",
            "produto_id",
            "produto_nome",
            "produto_preco",
            "quantidade",
            "subtotal"
        ]


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


class CancelarPedidoSerializer(serializers.Serializer):
    pedido = serializers.PrimaryKeyRelatedField(queryset=Pedido.objects.none())
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if not user:
            return

        self.fields["pedido"].queryset = Pedido.objects.filter(
            user=user,
            status__in=["pendente", "preparando"]
        )


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

        endereco = user.enderecos.first()
        if not endereco:
            raise serializers.ValidationError("Adicione um endereço antes de finalizar o pedido.")

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
                metodo_pagamento=metodo_pagamento,
                endereco=endereco  
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

        carrinho.items.all().delete()

        return pedidos_criados



class AtualizarStatusPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = ["status"]
        extra_kwargs = {
            "status": {"style": {"base_template": "select.html"}}
        }

class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = "__all__"
        read_only_fields = ["user"]

class EnderecoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = ["rua", "numero", "bairro", "cidade", "estado", "cep", "complemento"]


class PedidoLojaSerializer(serializers.ModelSerializer):
    endereco = EnderecoSerializer(read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "criado_em",
            "status",
            "total",
            "user",
            "loja",
            "metodo_pagamento",
            "endereco"
        ]
        read_only_fields = fields

class PagamentoSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())    
    class Meta:
        model = Pagamento
        fields = [
            "id",
            "user",
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