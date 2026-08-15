import uuid

from django.db import models

from commanders.models import Commander
from players.models import Player


class RetiredDeck(models.Model):
    player = models.ForeignKey(Player, on_delete=models.PROTECT, db_column="player_id")
    commander = models.ForeignKey(Commander, on_delete=models.PROTECT, db_column="commander_id")
    source = models.TextField(default="manual")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "retired_decks"
        # Node's schema uses (player_id, commander_id) as a composite primary
        # key; Django 5.1 has no composite-PK support, so a surrogate id plus
        # this uniqueness constraint gets the same guarantee.
        constraints = [
            models.UniqueConstraint(fields=["player", "commander"], name="uq_retired_decks_player_commander")
        ]

    def __str__(self):
        return f"{self.player_id} / {self.commander_id}"


class Deck(models.Model):
    """A specific player's build of a commander. Two different players can each
    own their own Deck for the same Commander — ownership, not the commander
    alone, is what makes a build unique."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Player, on_delete=models.PROTECT, db_column="owner_id", related_name="decks")
    commander = models.ForeignKey(
        Commander, on_delete=models.PROTECT, db_column="commander_id", related_name="decks"
    )
    name = models.TextField(null=True, blank=True)
    source = models.TextField(default="manual")
    moxfield_deck_id = models.TextField(null=True, blank=True)
    moxfield_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "decks"
        indexes = [
            models.Index(fields=["owner"], name="idx_decks_owner_id"),
            models.Index(fields=["commander"], name="idx_decks_commander_id"),
        ]

    def __str__(self):
        return self.name or f"{self.commander.name} ({self.owner.name})"


class DeckCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, db_column="deck_id", related_name="cards")
    card_name = models.TextField()
    set_code = models.TextField(null=True, blank=True)
    collector_number = models.TextField(null=True, blank=True)
    quantity = models.SmallIntegerField(default=1)
    is_foil = models.BooleanField(default=False)
    is_commander = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "deck_cards"
        ordering = ["card_name"]
        indexes = [models.Index(fields=["deck"], name="idx_deck_cards_deck_id")]

    def __str__(self):
        return self.card_name
