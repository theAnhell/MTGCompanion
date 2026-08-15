from django.contrib import admin

from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("card_name", "action", "deck", "player", "inclusion_rate", "status", "applied_at")
    list_filter = ("action", "status")
    search_fields = ("card_name", "player__name", "deck__commander__name")
