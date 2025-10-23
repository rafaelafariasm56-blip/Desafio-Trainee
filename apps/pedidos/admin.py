from django.contrib import admin
from .models import Carrinho, CarrinhoItem, Pedido, PedidoItem

@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "criado_em")
    search_fields = ("user__username",)
    list_filter = ("criado_em",)
    readonly_fields = ("criado_em",)

@admin.register(CarrinhoItem)
class CarrinhoItemAdmin(admin.ModelAdmin):
    list_display = ("id", "carrinho", "produto", "data", "quantidade")
    search_fields = ("carrinho__user__username", "produto__name")
    list_filter = ("data",)
    autocomplete_fields = ("carrinho", "produto")

class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0
    readonly_fields = ("produto", "preco", "quantidade", "data")

@admin.register(Pedido)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "loja", "status", "total", "criado_em")
    list_filter = ("status", "criado_em", "loja")
    search_fields = ("code", "user__username", "loja__nome")
    readonly_fields = ("code", "criado_em", "total")
    inlines = [PedidoItemInline]

@admin.register(PedidoItem)
class PedidoItemAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "produto", "quantidade", "preco", "data")
    search_fields = ("pedido__code", "produto__nome")
    list_filter = ("data",)
    autocomplete_fields = ("pedido", "produto")
