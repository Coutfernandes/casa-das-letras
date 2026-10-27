"""Peças reutilizadas pelas telas do painel admin."""

from django.contrib import admin


class ReadOnlyAdmin(admin.ModelAdmin):
    """Tela só de consulta, para registros que nunca mudam depois de criados."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
