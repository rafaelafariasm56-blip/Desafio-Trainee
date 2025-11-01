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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pagamento")
    nome = models.CharField(max_length=255)
    detalhes = models.JSONField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
