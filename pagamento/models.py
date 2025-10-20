from django.db import models
from django.conf import settings

class FormaPagamento(models.Model):
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="formas_pagamento")
    nome = models.CharField(max_length=100)  #pix ou cartao 
    detalhes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.cliente.username}"
