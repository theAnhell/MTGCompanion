from django.db import models


class Player(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    name = models.TextField()
    username = models.TextField(null=True, blank=True)
    color = models.TextField(null=True, blank=True)
    is_you = models.BooleanField(default=False)
    is_random = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    patron_tier = models.SmallIntegerField(null=True, blank=True)
    discord_user_id = models.TextField(null=True, blank=True)
    friend_code = models.TextField(null=True, blank=True)
    merged_into = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="merged_into_id",
        related_name="aliases",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "players"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["merged_into"], name="idx_players_merged_into_id"),
        ]

    def __str__(self):
        return self.name
