from django.contrib import admin

from .models import Commander


@admin.register(Commander)
class CommanderAdmin(admin.ModelAdmin):
    list_display = ("name", "deck_name", "disabled")
    search_fields = ("name", "deck_name")
