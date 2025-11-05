from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(max_length=16, unique=True, blank=False,null=False)
    nome = models.CharField(max_length = 100, blank=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=30, unique=True, blank=False)
    loja = models.BooleanField(default=False)
    
    def __Str__(self):
        return self.username

class Pagamento(models.Model):
    METODO_CHOICES = [
        ('cartao', 'Cartão de Crédito/Débito'),
        ('pix', 'Pix'),
        ('dinheiro', 'Dinheiro'),
        ('outro', 'Outro'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pagamentos")
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    nome_no_cartao = models.CharField(max_length=100, blank=True, null=True)
    numero_cartao = models.CharField(max_length=20, blank=True, null=True)
    validade = models.CharField(max_length=7, blank=True, null=True)  # MM/AAAA
    cvv = models.CharField(max_length=4, blank=True, null=True)
    chave_pix = models.CharField(max_length=255, blank=True, null=True)
    observacao = models.CharField(max_length=255, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_metodo_display()} - {self.user.username}"