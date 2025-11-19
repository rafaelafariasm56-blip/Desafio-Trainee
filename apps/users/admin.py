from django.contrib import admin
from apps.pedidos.models import Carrinho, CarrinhoItem, Pedido, PedidoItem


class CarrinhoItemInline(admin.TabularInline):
    model = CarrinhoItem
    extra = 1
    autocomplete_fields = ("produto",)


@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total")
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
    inlines = [CarrinhoItemInline]

    readonly_fields = ("total",)


class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 1
    autocomplete_fields = ("produto",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "loja", "status", "total", "criado_em")
    list_filter = ("status", "loja")
    search_fields = ("user__username", "loja__nome")
    autocomplete_fields = ("user", "loja", "metodo_pagamento", "endereco")
    inlines = [PedidoItemInline]
    readonly_fields = ("criado_em",)


@admin.register(PedidoItem)
class PedidoItemAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "produto", "preco", "quantidade", "subtotal")
    search_fields = ("pedido__id", "produto__nome")
    autocomplete_fields = ("pedido", "produto")

    def subtotal(self, obj):
        return obj.preco * obj.quantidade
