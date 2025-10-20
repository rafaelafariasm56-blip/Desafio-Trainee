from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente'
        LOJA = 'LOJA', 'Loja'

    base_role = Role.CLIENTE

    role = models.CharField(max_length=50, choices=Role.choices, default=base_role)


    def __str__(self):
        return f"{self.username} ({self.role})"


class PerfilCliente(models.Model):
    nome = models.CharField(max_length=50)    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_cliente")
    cpf = models.CharField(max_length=11, unique=True)
    data_nascimento = models.DateField(null=True)
    celular = models.CharField(max_length=15)

    def __str__(self):
        return f"Cliente: {self.user.username}"


class PerfilLoja(models.Model):
    nome = models.CharField(max_length=50)    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_loja")
    celular = models.CharField(max_length=15)
    cnpj = models.CharField(max_length=14, unique=True)
    endereco = models.CharField(max_length=300, blank=True)
    aberto = models.BooleanField(default=True)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return f"Loja: {self.user.username}"
