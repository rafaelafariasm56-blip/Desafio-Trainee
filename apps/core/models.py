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
    loja = models.OneToOneField(LojaPerfil, on_delete=models.CASCADE, related_name="cardapio")
    produtos = models.ManyToManyField('Produto', related_name='cardapios')

    def __str__(self):
        return f"Cardápio de {self.loja.nome}"