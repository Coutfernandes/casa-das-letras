"""Movimentações da carteira no painel admin (somente leitura)."""

from django.contrib import admin

from core.admin import ReadOnlyAdmin

from .models import WalletEntry


@admin.register(WalletEntry)
class WalletEntryAdmin(ReadOnlyAdmin):
    list_display = ["user", "kind", "amount", "lot", "created_at"]
    list_filter = ["kind"]
