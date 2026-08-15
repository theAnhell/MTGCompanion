from django.contrib import admin

from .models import Commander, CommanderCardStat


@admin.register(Commander)
class CommanderAdmin(admin.ModelAdmin):
    list_display = ("name", "deck_name", "edhrec_slug", "edhrec_synced_at", "disabled")
    search_fields = ("name", "deck_name")


@admin.register(CommanderCardStat)
class CommanderCardStatAdmin(admin.ModelAdmin):
    list_display = ("card_name", "commander", "category", "inclusion_rate", "num_decks", "potential_decks")
    list_filter = ("category",)
    search_fields = ("card_name", "commander__name")
