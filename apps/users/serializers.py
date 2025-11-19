from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Endereco
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = ["cep", "rua", "numero", "bairro", "cidade", "estado"]

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, required=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "loja", "nome")

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):  
        endereco_data = validated_data.pop("endereco", None)

        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            nome=validated_data['nome'],
            loja=validated_data.get('loja', False),
            is_active=True,  
        )
        user.set_password(validated_data['password'])  
        user.save()

        if endereco_data:
            from apps.users.models import Endereco
            Endereco.objects.create(user=user, **endereco_data)

        if user.loja:
            from apps.core.models import LojaPerfil
            LojaPerfil.objects.get_or_create(user=user, nome=user.username)

        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'nome', 'loja', 'celular', 'password']
        extra_kwargs = {
            'email': {'required': False},
            'nome': {'required': False},
            'loja': {'required': False},
            'celular': {'required': False},
            'password': {'write_only': True},
        }

    def update(self, instance, validated_data):
        for field in ['email', 'nome', 'loja', 'celular']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)

        instance.save()
        return instance

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        is_loja = hasattr(user, "lojaperfil")

        token["is_loja"] = is_loja
        token["loja_id"] = user.lojaperfil.id if is_loja else None

        return token
    

    
