import uuid

from django.db import models

from players.models import Player


class BinderCard(models.Model):
    """A card a player owns outside of any specific deck — their loose
    collection/"binder". Together with a player's Decks, this is their full
    collection for recommendation purposes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, db_column="player_id", related_name="binder_cards")
    card_name = models.TextField()
    set_code = models.TextField(null=True, blank=True)
    collector_number = models.TextField(null=True, blank=True)
    quantity = models.SmallIntegerField(default=1)
    is_foil = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "binder_cards"
        ordering = ["card_name"]
        indexes = [models.Index(fields=["player"], name="idx_binder_cards_player_id")]

    def __str__(self):
        return self.card_name
