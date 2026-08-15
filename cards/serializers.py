from rest_framework import serializers


class SyncStatusSerializer(serializers.Serializer):
    cardCount = serializers.IntegerField(source="card_count")
    syncedAt = serializers.DateTimeField(source="synced_at", allow_null=True)
