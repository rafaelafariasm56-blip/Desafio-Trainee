from django.contrib import admin
from apps.core.models import Produto, Disponibilidade, LojaPerfil

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    search_fields = ['nome']  

@admin.register(LojaPerfil)
class PerfilLojaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'user']

@admin.register(Disponibilidade)
class DisponibilidadeAdmin(admin.ModelAdmin):
    list_display = ['id', 'produto', 'data', 'quantidade']  #ajustar dps
