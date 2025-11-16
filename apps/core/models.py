from django.db import models


class LojaPerfil(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="lojaperfil")
    nome = models.CharField(max_length=255)
    endereco = models.ForeignKey("users.Endereco", on_delete=models.CASCADE, null=True, blank=True, related_name="lojas")
    aberta = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Produto(models.Model):
    loja = models.ForeignKey("core.LojaPerfil", on_delete=models.CASCADE, related_name="produtos")
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=0)  
    disponivel = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome


class Cardapio(models.Model):
    loja = models.OneToOneField(LojaPerfil, on_delete=models.CASCADE, related_name="cardapio")
    produtos = models.ManyToManyField(Produto, related_name="cardapios")

    def __str__(self):
        return f"Cardápio de {self.loja.nome}"

