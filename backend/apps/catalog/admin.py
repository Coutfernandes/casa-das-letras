"""Livros no painel admin."""

from django.contrib import admin

from .models import CatalogItemSnapshot


@admin.register(CatalogItemSnapshot)
class CatalogItemSnapshotAdmin(admin.ModelAdmin):
    list_display = ["title", "first_publish_year", "ol_work_key", "created_at"]
    search_fields = ["title", "ol_work_key"]
