from django.contrib import admin
from apps.users.models import User, Pagamento, Endereco


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "nome", "email", "celular", "loja", "is_active")
    list_filter = ("loja", "is_active", "is_staff")
    search_fields = ("username", "email", "nome")
    ordering = ("username",)


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "metodo", "ativo")
    list_filter = ("metodo", "ativo")
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "rua", "numero", "cidade", "estado")
    list_filter = ("estado", "cidade")
    search_fields = ("rua", "bairro", "cidade", "estado", "user__username")
    autocomplete_fields = ("user",)
