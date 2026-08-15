from django.contrib import admin

from .models import Game, GamePlayer


class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    extra = 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("name", "created_on", "total_turns", "game_time_in_minutes")
    inlines = [GamePlayerInline]
