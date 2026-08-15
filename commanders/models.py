from django.contrib.postgres.fields import ArrayField
from django.db import models


class Commander(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    scryfall_id = models.UUIDField(null=True, blank=True)
    name = models.TextField()
    colors = ArrayField(models.TextField(), null=True, blank=True)
    image_uri = models.TextField(null=True, blank=True)
    image_uri_partner = models.TextField(null=True, blank=True)
    edhrec_rank = models.IntegerField(null=True, blank=True)
    cmc = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    mythic_rank = models.SmallIntegerField(null=True, blank=True)
    disabled = models.BooleanField(default=False)
    deck_id = models.TextField(null=True, blank=True)
    deck_name = models.TextField(null=True, blank=True)
    decklist_url = models.TextField(null=True, blank=True)
    art_image_uri = models.TextField(null=True, blank=True)
    art_image_uri_partner = models.TextField(null=True, blank=True)
    # EDHREC's own URL slug, e.g. "queen-marchesa" — auto-derived by default,
    # but partner/background pairs use a combined-slug URL that can't be
    # reliably guessed, so this allows a manual override (same curation
    # pattern as data/moxfield-decks.json's commanderId mapping).
    edhrec_slug = models.TextField(null=True, blank=True)
    edhrec_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commanders"
        ordering = ["name"]
        indexes = [models.Index(fields=["name"], name="idx_commanders_name")]

    def __str__(self):
        return self.name


class CommanderCardStat(models.Model):
    """Cached per-commander card inclusion rates from EDHREC, refreshed by
    commanders.services.sync_commander_card_stats. Full-replaced per commander
    on each sync, not diffed."""

    commander = models.ForeignKey(
        Commander, on_delete=models.CASCADE, db_column="commander_id", related_name="card_stats"
    )
    card_name = models.TextField()
    category = models.TextField()
    num_decks = models.IntegerField()
    potential_decks = models.IntegerField()
    synergy = models.FloatField(null=True, blank=True)
    inclusion_rate = models.DecimalField(max_digits=5, decimal_places=1)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commander_card_stats"
        ordering = ["-inclusion_rate"]
        indexes = [models.Index(fields=["commander"], name="idx_cmdr_card_stats_cmdr_id")]
        constraints = [
            models.UniqueConstraint(fields=["commander", "card_name"], name="uq_commander_card_stats_commander_card")
        ]

    def __str__(self):
        return f"{self.card_name} ({self.commander_id})"
