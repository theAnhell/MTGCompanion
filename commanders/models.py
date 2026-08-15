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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commanders"
        ordering = ["name"]
        indexes = [models.Index(fields=["name"], name="idx_commanders_name")]

    def __str__(self):
        return self.name
