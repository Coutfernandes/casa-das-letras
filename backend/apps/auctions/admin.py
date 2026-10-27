"""Lotes no painel admin."""

from django.contrib import admin

from .models import Lot


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ["__str__", "auctioneer", "status", "current_price", "bid_count", "ends_at"]
    list_filter = ["status"]
    search_fields = ["item__title"]
    readonly_fields = [
        "original_ends_at",
        "current_price",
        "leader",
        "bid_count",
        "last_bid_hash",
        "anchor_signature",
        "winner",
        "final_price",
        "closed_at",
        "created_at",
    ]
