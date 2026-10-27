"""Comprovantes no painel admin (somente leitura)."""

from django.contrib import admin

from core.admin import ReadOnlyAdmin

from .models import Receipt


@admin.register(Receipt)
class ReceiptAdmin(ReadOnlyAdmin):
    list_display = ["lot", "winner_alias", "amount", "issued_at"]
