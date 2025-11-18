from django.conf import settings
from django.db import models
from apps.users.models import User
from apps.core.models import Produto

class Carrinho(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="carrinho")

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class CarrinhoItem(models.Model):
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name="items")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    adicionado_em = models.DateTimeField(auto_now_add=True)


    @property
    def subtotal(self):
        return self.produto.preco * self.quantidade



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
    endereco = models.ForeignKey("users.Endereco", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.user.username} ({self.status}) - R$ {self.total:.2f}"

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
