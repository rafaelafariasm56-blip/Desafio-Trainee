from django.conf import settings
from django.db import models
from apps.users.models import User
from apps.core.models import Produto
from apps.core.serializers import ProdutoSerializer
from decimal import Decimal

import uuid

class Carrinho(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carrinho"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrinho de {self.user.username}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class CarrinhoItem(models.Model):
    carrinho = models.ForeignKey(
        Carrinho,
        on_delete=models.CASCADE,
        related_name="items"
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="carrinho_items"
    )
    quantidade = models.PositiveIntegerField(default=1)
    data = models.DateField(blank=True, null=True)
    adicionado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("carrinho", "produto", "data")
        ordering = ["adicionado_em"]

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"

    @property
    def subtotal(self):
        return Decimal(self.quantidade) * self.produto.preco
    
def gerar_code():
    return uuid.uuid4().hex[:12].upper()

class Pedido(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("preparando", "Preparando"),
        ("a caminho", "A caminho"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="pedidos")
    loja = models.ForeignKey("core.LojaPerfil", on_delete=models.CASCADE, related_name="pedidos")
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pagamento = models.ForeignKey("users.Pagamento", on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=12, unique=True, default=gerar_code)

    def __str__(self):
        return f"Pedido #{self.code} - {self.user.username} ({self.status})"

class PedidoItem(models.Model):
    pedido = models.ForeignKey("Pedido", on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey("core.Produto", on_delete=models.CASCADE)
    data = models.DateField(
        help_text="Data de retirada/entrega", blank=True, null=True
    )
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.preco * self.quantidade

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} - R${self.preco}"
