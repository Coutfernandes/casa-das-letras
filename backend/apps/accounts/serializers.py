"""Conversão entre usuários e JSON, com validação dos dados recebidos."""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


def normalize(email):
    """E-mail sempre em minúsculas e sem espaços: Ana@X.com e ana@x.com são o mesmo."""
    return email.strip().lower()


class UserSerializer(serializers.ModelSerializer):
    """O que o front recebe sobre o usuário logado. Nunca inclui a senha."""

    class Meta:
        model = User
        fields = ["id", "email", "name", "role", "public_alias"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Cadastro: e-mail, nome, papel e senha."""

    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ["email", "name", "role", "password"]

    def validate_email(self, value):
        email = normalize(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def validate(self, attrs):
        # Os validadores do settings.py comparam a senha com o e-mail e o nome,
        # por isso recebem um usuário (ainda não salvo) com esses dados.
        candidate = User(email=attrs["email"], name=attrs["name"])
        validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Login: confere e-mail e senha e devolve o usuário em attrs['user']."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=normalize(attrs["email"]),
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("E-mail ou senha incorretos.")
        attrs["user"] = user
        return attrs
