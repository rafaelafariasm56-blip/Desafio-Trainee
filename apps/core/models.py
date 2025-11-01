from django.db import models
from apps.users.models import User

class LojaPerfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    endereco = models.CharField(max_length=500, blank=True)  
    aberta = models.BooleanField(default=True)

    def __str__(self):
        return self.nome  

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    loja = models.ForeignKey(LojaPerfil, on_delete=models.CASCADE)
    descricao = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    active = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
    
class Cardapio(models.Model):
    loja = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.loja.username})"
    

class CardapioItem(models.Model):
    cardapio = models.ForeignKey(Cardapio, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    disponivel = models.BooleanField(default=True)
    dias_disponiveis = models.JSONField(default=list, help_text="Lista de dias disponíveis (ex: ['segunda', 'sexta'])")

    def __str__(self):
        return f"{self.produto.nome} - {self.cardapio.nome}"