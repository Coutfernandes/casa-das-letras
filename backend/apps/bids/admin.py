"""Lances no painel admin (somente leitura)."""

from django.contrib import admin

from core.admin import ReadOnlyAdmin

from .models import Bid


@admin.register(Bid)
class BidAdmin(ReadOnlyAdmin):
    list_display = ["lot", "sequence", "bidder", "amount", "created_at"]
    list_filter = ["lot"]