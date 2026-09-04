from rest_framework import serializers

from .models import Commander
from .services import get_edhrec_url


class CommanderSerializer(serializers.ModelSerializer):
    imageUri = serializers.CharField(source="image_uri", allow_null=True)
    edhrecRank = serializers.IntegerField(source="edhrec_rank", allow_null=True)
    cmc = serializers.DecimalField(max_digits=4, decimal_places=1, allow_null=True, coerce_to_string=False)
    deckName = serializers.CharField(source="deck_name", allow_null=True)
    decklistUrl = serializers.CharField(source="decklist_url", allow_null=True)
    edhrecUrl = serializers.SerializerMethodField()

    class Meta:
        model = Commander
        fields = ["id", "name", "colors", "imageUri", "edhrecRank", "cmc", "deckName", "decklistUrl", "edhrecUrl"]

    def get_edhrecUrl(self, obj) -> str:
        return get_edhrec_url(obj)


class EdhrecSyncStatusSerializer(serializers.Serializer):
    commanderCount = serializers.IntegerField(source="commander_count")
    staleCount = serializers.IntegerField(source="stale_count")
    oldestSyncedAt = serializers.DateTimeField(source="oldest_synced_at", allow_null=True)
    newestSyncedAt = serializers.DateTimeField(source="newest_synced_at", allow_null=True)
    failedCommanderNames = serializers.ListField(
        source="failed_commander_names", child=serializers.CharField()
    )
