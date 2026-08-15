from django.db import models

from commanders.models import Commander
from players.models import Player


class Game(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    name = models.TextField()
    notes = models.TextField(null=True, blank=True)
    tags = models.TextField(null=True, blank=True)
    discord_server_url = models.TextField(null=True, blank=True)
    discord_server_name = models.TextField(null=True, blank=True)
    # Stored naively, matching the Node import's "no TZ conversion" behaviour.
    created_on = models.DateTimeField()
    game_type = models.SmallIntegerField(null=True, blank=True)
    game_status = models.SmallIntegerField(null=True, blank=True)
    win_condition = models.SmallIntegerField(null=True, blank=True)
    platform = models.SmallIntegerField(null=True, blank=True)
    bracket = models.SmallIntegerField(null=True, blank=True)
    total_turns = models.SmallIntegerField(null=True, blank=True)
    game_time_in_minutes = models.IntegerField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    key_cards = models.JSONField(null=True, blank=True)
    custom_stats = models.JSONField(null=True, blank=True)
    turn_logs = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "games"
        ordering = ["-created_on"]
        indexes = [models.Index(fields=["created_on"], name="idx_games_created_on")]

    def __str__(self):
        return self.name


class GamePlayer(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, db_column="game_id", related_name="players"
    )
    player = models.ForeignKey(
        Player, on_delete=models.PROTECT, db_column="player_id", related_name="game_players"
    )
    commander = models.ForeignKey(
        Commander, on_delete=models.PROTECT, db_column="commander_id", related_name="game_players"
    )
    commander_partner = models.ForeignKey(
        Commander,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="commander_partner_id",
        related_name="partnered_game_players",
    )
    has_partners = models.BooleanField(default=False)
    turn_order = models.SmallIntegerField(null=True, blank=True)
    mulligans = models.SmallIntegerField(null=True, blank=True)
    is_winner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_players"
        indexes = [
            models.Index(fields=["game"], name="idx_game_players_game_id"),
            models.Index(fields=["player"], name="idx_game_players_player_id"),
            models.Index(fields=["commander"], name="idx_game_players_commander_id"),
            models.Index(fields=["commander_partner"], name="idx_game_players_cmdr_partner"),
            models.Index(fields=["player", "commander"], name="idx_game_players_player_cmdr"),
            models.Index(fields=["player", "is_winner"], name="idx_game_players_player_winner"),
        ]
