from django.contrib import admin
from .models import LojaPerfil, Produto, Cardapio


@admin.register(LojaPerfil)
class LojaPerfilAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "user", "aberta")
    list_filter = ("aberta",)
    search_fields = ("nome", "user__username")
    autocomplete_fields = ("user", "endereco")


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "loja", "preco", "quantidade", "disponivel", "active", "criada_em")
    list_filter = ("disponivel", "active", "loja")
    search_fields = ("nome", "descricao", "loja__nome")
    autocomplete_fields = ("loja",)
    readonly_fields = ("criada_em", "atualizada_em")


class ProdutoInline(admin.TabularInline):
    model = Cardapio.produtos.through
    extra = 1
    autocomplete_fields = ("produto",)


@admin.register(Cardapio)
class CardapioAdmin(admin.ModelAdmin):
    list_display = ("id", "loja")
    autocomplete_fields = ("loja",)
    inlines = [ProdutoInline]
