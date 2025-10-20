from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, PerfilCliente, PerfilLoja


class PerfilClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilCliente
        fields = ["nome", "cpf", "data_nascimento", "celular"]


class PerfilLojaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilLoja
        fields = ["nome", "celular", "cnpj", "endereco", "aberto", "descricao"]


class UserSerializer(serializers.ModelSerializer):
    perfil_cliente = PerfilClienteSerializer(required=False)
    perfil_loja = PerfilLojaSerializer(required=False)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "role",
            "perfil_cliente",
            "perfil_loja",
        ]

    def create(self, validated_data):
        perfil_cliente_data = validated_data.pop("perfil_cliente", None)
        perfil_loja_data = validated_data.pop("perfil_loja", None)

        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user.role == User.Role.CLIENTE and perfil_cliente_data:
            PerfilCliente.objects.create(user=user, **perfil_cliente_data)
        elif user.role == User.Role.LOJA and perfil_loja_data:
            PerfilLoja.objects.create(user=user, **perfil_loja_data)

        return user

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.role == User.Role.CLIENTE and hasattr(instance, "perfil_cliente"):
            rep["perfil_cliente"] = PerfilClienteSerializer(instance.perfil_cliente).data
        elif instance.role == User.Role.LOJA and hasattr(instance, "perfil_loja"):
            rep["perfil_loja"] = PerfilLojaSerializer(instance.perfil_loja).data
        return rep
