"""Usuários no painel admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    ordering = ["email"]
    list_display = ["email", "name", "role", "public_alias", "is_active"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["email", "name", "public_alias"]
    readonly_fields = ["public_alias", "date_joined", "last_login"]

    # Tela de edição.
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Perfil", {"fields": ["name", "role", "public_alias"]}),
        (
            "Permissões",
            {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]},
        ),
        ("Datas", {"fields": ["last_login", "date_joined"]}),
    ]

    # Tela de cadastro.
    add_fieldsets = [
        (
            None,
            {"classes": ["wide"], "fields": ["email", "name", "role", "password1", "password2"]},
        ),
    ]
