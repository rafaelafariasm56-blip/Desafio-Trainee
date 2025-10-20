from django.db import models
from django.conf import settings
from cardapio.models import Oferta
import uuid

class Pedido(models.Model):
    STATUS = [
        ("PENDENTE", "Pendente"),
        ("CONFIRMADO", "Confirmado"),
        ("PREPARANDO", "Preparando"),
        ("ENTREGUE", "Entregue"),
        ("CANCELADO", "Cancelado"),
    ]

    codigo = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pedidos")
    loja = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pedidos_recebidos")
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default="PENDENTE")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Pedido {self.codigo} - {self.cliente.username}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    oferta = models.ForeignKey(Oferta, on_delete=models.CASCADE, default=1)
    quantidade = models.PositiveIntegerField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
