from django.contrib import admin

from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("name", "type_line", "roles", "cmc")
    search_fields = ("name",)
