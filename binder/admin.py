from django.contrib import admin

from .models import BinderCard


@admin.register(BinderCard)
class BinderCardAdmin(admin.ModelAdmin):
    list_display = ("card_name", "player", "quantity", "is_foil")
    search_fields = ("card_name", "player__name")
