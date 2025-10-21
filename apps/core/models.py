from django.db import models
from users.models import User

class LojaPerfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_loja")
    nome = models.CharField(max_length=255)
    endereço = models.CharField(max_length=500, blank=True)
    aberta = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Produto(models.Model):
    loja = models.ForeignKey(LojaPerfil, on_delete=models.CASCADE, related_name="produtos")
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    active = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

class Disponibilidade(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="availabilities")
    data = models.DateField()
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade = models.PositiveIntegerField()

    class Meta:
        unique_together = ("produtos", "datas")
