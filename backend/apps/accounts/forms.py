"""Formulários do painel admin para o usuário personalizado."""

from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class UserAdminCreationForm(UserCreationForm):
    """Cadastro pelo admin: e-mail, nome, papel e senha (duas vezes)."""

    class Meta:
        model = User
        fields = ["email", "name", "role"]


class UserAdminChangeForm(UserChangeForm):
    """Edição pelo admin. A senha aparece só como hash, nunca em texto."""

    class Meta:
        model = User
        fields = "__all__"
