from django.contrib import admin

from .models import DeckCard, RetiredDeck


@admin.register(RetiredDeck)
class RetiredDeckAdmin(admin.ModelAdmin):
    list_display = ("player", "commander", "source", "created_at")


@admin.register(DeckCard)
class DeckCardAdmin(admin.ModelAdmin):
    list_display = ("card_name", "commander", "quantity", "is_foil", "is_commander")
    search_fields = ("card_name",)
