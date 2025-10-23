from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Sum, F
from .models import Carrinho, CarrinhoItem, Pedido, PedidoItem
from .serializers import CarrinhoSerializer, CarrinhoItemSerializer, PedidoSerializer
from core.models import Disponibilidade, LojaPerfil
from users.models import Pagamento
from users.permissions import IsClient, IsLoja
from datetime import date

class CarrinhoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsClient]

    def list(self, request):
        carrinho, _ = Carrinho.objects.get_or_create(user=request.user)
        serializer = CarrinhoSerializer(Carrinho)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        carrinho, _ = Carrinho.objects.get_or_create(user=request.user)
        serializer = CarrinhoItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        produto = serializer.validated_data["produto"]
        data_selecionada = serializer.validated_data["data"]

        items = Carrinho.items.select_related("produto_estabelecimento").all()
        if items.exists():
            first_est = items.first().produto.establishment
            if produto.establishment != first_est:
                return Response({"detail": "Carrinho already contains items from another establishment"}, status=400)

        try:
            avail = Disponibilidade.objects.get(produto=produto, date=data_selecionada)
        except Disponibilidade.DoesNotExist:
            return Response({"detail": "Produto indisponivel nesta data"}, status=400)

        if serializer.validated_data["quantity"] > avail.quantity:
            return Response({"detail": "Not enough stock"}, status=400)

        Carrinho_Item, _ = CarrinhoItem.objects.update_or_create(
            cart=Carrinho, produto=produto, date=data_selecionada,
            defaults={"quantidade": serializer.validated_data["quantidade"]}
        )
        return Response(CarrinhoItemSerializer(Carrinho_Item).data, status=201)

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        carrinho, _ = Carrinho.objects.get_or_create(user=request.user)
        produto_id = request.data.get("produto")
        data_selecionada = request.data.get("data")
        CarrinhoItem.objects.filter(carrinho=carrinho, produto_id=produto_id, data=data_selecionada).delete()
        return Response(status=204)

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        user = request.user
        carrinho, _ = Carrinho.objects.get_or_create(user=user)
        items = list(carrinho.items.select_related("produto").all())
        if not items:
            return Response({"detail": "Carrinho vazio"}, status=400)

        est = items[0].produto.loja
        if not est.open:
            return Response({"Detalhe": "Estabelecimento está fechado"}, status=400)

        pm_id = request.data.get("metodo_pagamento")
        pagamento_metodo = None
        if pm_id:
            try:
                pagamento_metodo = Pagamento.objects.get(id=pm_id, user=user, active=True)
            except Pagamento.DoesNotExist:
                return Response({"detalhe": "Método de pagamento inválido"}, status=400)
        with transaction.atomic():
            total = 0
            for it in items:
                avail = Disponibilidade.objects.select_for_update().get(product=it.product, date=it.date)
                if avail.quantity < it.quantity:
                    return Response({"detail": f"Sem estoque {it.product.name} para {it.date}"}, status=400)
                total += float(avail.price) * it.quantity

            order = Pedido.objects.create(
                user=user,
                loja=est,
                total=total,
                pagamento_metodo=pagamento_metodo,
                code=PedidoSerializer.generate_code(PedidoSerializer)
            )

            for it in items:
                avail = Disponibilidade.objects.select_for_update().get(product=it.product, date=it.date)
                CarrinhoItem.objects.create(
                    order=order,
                    produto=it.produto,
                    data=it.daata,
                    preco=avail.preco,
                    quantidade=it.quantidade
                )
                avail.quantity -= it.quantity
                avail.save()

            carrinho.items.all().delete()

        return Response({"pedido_id": order.id, "code": order.code}, status=201)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().select_related("loja","user")
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_establishment:
            est = LojaPerfil.objects.get(user=user)
            return Pedido.objects.filter(loja=est, status__in=["pendente","preparando","a caminho"]).order_by("criado_em")
        return Pedido.objects.filter(user=user).order_by("criado_em")

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        order = self.get_object()
        if not request.user.is_loja or order.loja.user != request.user:
            return Response({"detail": "Not allowed"}, status=403)
        new_status = request.data.get("status")
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({"detail": "Invalid status"}, status=400)
        order.status = new_status
        order.save()
        return Response({"status": order.status})

    @action(detail=False, methods=["get"])
    def history(self, request):
        qs = self.get_queryset().order_by("-criado_em")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = PedidoSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PedidoSerializer(qs, many=True)
        return Response(serializer.data)

class BillingReportView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsLoja]

    @action(detail=False, methods=["get"])
    def receita(self, request):
        comeco = request.query_params.get("start_date")
        fim = request.query_params.get("end_date")
        est = LojaPerfil.objects.get(user=request.user)
        qs = PedidoItem.objects.filter(order__establishment=est, order__status__in=["entregue","a caminho","preparando","pendente"])
        if comeco:
            qs = qs.filter(date__gte=comeco)
        if fim:
            qs = qs.filter(date__lte=fim)
        total = qs.aggregate(total_revenue=Sum(F("preco")*F("quantidade")))["total_receita"] or 0
        por_dia = qs.values("data").annotate(revenue=Sum(F("preco")*F("quantidade"))).order_by("-date")
        return Response({"total": total, "por_dia": list(por_dia)})
