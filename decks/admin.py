from django.contrib import admin

from .models import Deck, DeckCard, RetiredDeck


@admin.register(RetiredDeck)
class RetiredDeckAdmin(admin.ModelAdmin):
    list_display = ("player", "commander", "source", "created_at")


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner", "commander", "source", "created_at")
    search_fields = ("name", "owner__name", "commander__name")


@admin.register(DeckCard)
class DeckCardAdmin(admin.ModelAdmin):
    list_display = ("card_name", "deck", "quantity", "is_foil", "is_commander")
    search_fields = ("card_name",)
