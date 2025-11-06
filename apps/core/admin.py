from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User
from .models import LojaPerfil, Produto, Cardapio


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Apenas campos que existem no modelo User
    list_display = ("username", "email", "nome", "loja")
    search_fields = ("username", "email", "nome")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informações pessoais", {"fields": ("nome", "email", "celular")}),
        ("Permissões", {"fields": ("loja", "groups", "user_permissions")}),
        ("Datas importantes", {"fields": ("ultimo_login", "data_criada")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "nome", "password1", "password2", "loja"),
        }),
    )


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
    readonly_fields = ("criada_em",)
    ordering = ("-criada_em",)
    fieldsets = (
        ("Informações", {"fields": ("loja", "nome", "descricao", "slug", "active")}),
        ("Metadados", {"fields": ("criada_em",)}),
    )
    autocomplete_fields = ("loja",)


@admin.register(Cardapio)
class CardapioAdmin(admin.ModelAdmin):
    list_display = ('id', 'loja')
    search_fields = ('loja__nome',)
    readonly_fields = ('loja',)
    ordering = ('id',)