from django.contrib import admin
from .models import User, PerfilCliente, PerfilLoja

admin.site.register(User)
admin.site.register(PerfilCliente)
admin.site.register(PerfilLoja)
