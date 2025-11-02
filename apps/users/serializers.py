from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.users.models import User, Pagamento


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, required=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "loja", "nome")

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            nome=validated_data['nome'],
            loja=validated_data.get('loja', False),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'nome', 'loja', 'celular']
        extra_kwargs = {
            'email': {'required': False},
            'nome': {'required': False},
            'loja': {'required': False},
            'celular': {'required': False},
        }

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.nome = validated_data.get('nome', instance.nome)
        instance.loja = validated_data.get('loja', instance.loja)
        instance.celular = validated_data.get('celular', instance.celular)

        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)

        instance.save()
        return instance

class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = "__all__"
        read_only_fields = ("user",)
