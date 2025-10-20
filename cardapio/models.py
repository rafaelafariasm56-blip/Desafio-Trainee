from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Prato(models.Model):
    loja = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pratos")
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    imagem = models.URLField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.loja.username})"


class Oferta(models.Model):  
    prato = models.ForeignKey(Prato, on_delete=models.CASCADE, related_name="ofertas")
    data = models.DateField()
    quantidade_disponivel = models.PositiveIntegerField(default=0)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    ativa = models.BooleanField(default=True)

    class Meta:
        unique_together = ("prato", "data")
        ordering = ["data"]

    def __str__(self):
        return f"{self.prato.nome} - {self.data}"
