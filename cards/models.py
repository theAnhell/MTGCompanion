from django.contrib.postgres.fields import ArrayField
from django.db import models


class Card(models.Model):
    """Reference data from Scryfall's Oracle Cards bulk export, keyed by name
    to match how DeckCard/BinderCard/CommanderCardStat already reference
    cards. `roles` is computed locally (Scryfall's bulk data has no
    functional tags — those live only on the separate tagger.scryfall.com,
    with no bulk API) via cards.services.classify_roles, not raw Scryfall
    data."""

    name = models.TextField(primary_key=True)
    scryfall_id = models.UUIDField(null=True, blank=True)
    mana_cost = models.TextField(null=True, blank=True)
    # A handful of joke/Un-set cards have absurd CMC values (e.g. Gleemax at
    # 1,000,000), so this needs far more headroom than Commander.cmc.
    cmc = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
    type_line = models.TextField(null=True, blank=True)
    oracle_text = models.TextField(null=True, blank=True)
    color_identity = ArrayField(models.TextField(), null=True, blank=True)
    roles = ArrayField(models.TextField(), default=list, blank=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cards"
        ordering = ["name"]

    def __str__(self):
        return self.name
