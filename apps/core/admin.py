from django.contrib import admin
from .models import LojaPerfil, Produto, Cardapio, CardapioItem

# Inline para mostrar produtos dentro do perfil da loja
class ProdutoInline(admin.TabularInline):
    model = Produto
    extra = 0
    fields = ("nome", "active", "criada_em")
    readonly_fields = ("criada_em",)
    show_change_link = True


@admin.register(LojaPerfil)
class LojaPerfilAdmin(admin.ModelAdmin):
    list_display = ("nome", "user", "endereco", "aberta")
    list_filter = ("aberta",)
    search_fields = ("nome", "user__username", "endereco")
    ordering = ("nome",)
    inlines = [ProdutoInline]
    fieldsets = (
        ("Dados da Loja", {"fields": ("user", "nome", "endereco", "aberta")}),
    )


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "loja", "active", "criada_em")
    list_filter = ("loja", "active")
    search_fields = ("nome", "descricao", "loja__nome", "loja__user__username")
    prepopulated_fields = {"slug": ("nome",)}
    readonly_fields = ("criada_em",)
    ordering = ("-criada_em",)
    fieldsets = (
        ("Informações", {"fields": ("loja", "nome", "descricao", "slug", "active")}),
        ("Metadados", {"fields": ("criada_em",)}),
    )
    autocomplete_fields = ("loja",)


# Inline para mostrar CardapioItem dentro do Cardápio
class CardapioItemInline(admin.TabularInline):
    model = CardapioItem
    extra = 0
    fields = ("produto", "preco", "estoque", "disponivel", "dias_disponiveis")
    autocomplete_fields = ("produto",)
    show_change_link = True


@admin.register(Cardapio)
class CardapioAdmin(admin.ModelAdmin):
    list_display = ("nome", "get_loja", "data_criacao")
    list_filter = ("data_criacao",)
    search_fields = ("nome", "loja__nome", "loja__user__username")
    readonly_fields = ("data_criacao",)
    inlines = [CardapioItemInline]
    ordering = ("-data_criacao",)
    fieldsets = (
        ("Cardápio", {"fields": ("loja", "nome")}),
        ("Metadados", {"fields": ("data_criacao",)}),
    )
    autocomplete_fields = ("loja",)

    def get_loja(self, obj):
        # exibe username
        return getattr(obj.loja, "username", None)
    get_loja.short_description = "Loja"


@admin.register(CardapioItem)
class CardapioItemAdmin(admin.ModelAdmin):
    list_display = ("produto", "get_cardapio", "preco", "estoque", "disponivel")
    list_filter = ("disponivel", "cardapio__loja")
    search_fields = ("produto__nome", "cardapio__nome", "cardapio__loja__nome")
    ordering = ("-cardapio__data_criacao", "produto__nome")
    fields = ("cardapio", "produto", "preco", "estoque", "disponivel", "dias_disponiveis")
    autocomplete_fields = ("cardapio", "produto")

    def get_cardapio(self, obj):
        return obj.cardapio.nome
    get_cardapio.short_description = "Cardápio"
