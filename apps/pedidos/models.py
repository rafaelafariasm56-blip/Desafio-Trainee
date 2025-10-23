from django.db import models
from users.models import User, Pagamento
from core.models import Produto, LojaPerfil

class Carrinho(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrinho de {self.user.username}"


class CarrinhoItem(models.Model):

    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name="items")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    data = models.DateField(help_text="Data de disponibilidade escolhida")
    quantidade = models.PositiveIntegerField()

    class Meta:
        unique_together = ("cart", "product", "date")

    def __str__(self):
        return f"{self.quantity}x {self.product.name} ({self.date})"


class Pedido(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("preparando", "Preparando"),
        ("a caminho", "A caminho"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pedidos")
    loja = models.ForeignKey(LojaPerfil, on_delete=models.CASCADE, related_name="pedidos")
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pagamento = models.ForeignKey(Pagamento, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return f"Pedido #{self.code} - {self.user.username} ({self.status})"


class PedidoItem(models.Model):
    pedidos = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    data = models.DateField(help_text="Data de retirada/entrega")
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade = models.PositiveIntegerField()

    def subtotal(self):
        return self.preco * self.quantidade

    def __str__(self):
        return f"{self.quantidade}x {self.produto.name} - R${self.preco}"
