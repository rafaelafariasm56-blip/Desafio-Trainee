from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    loja = models.BooleanField(default=False)
    celular = models.CharField(max_length=20, blank=True, null=True)

class Pagamento(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pagamento")
    nome = models.CharField(max_length=255)
    detalhes = models.JSONField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
