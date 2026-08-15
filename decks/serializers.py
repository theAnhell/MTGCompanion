from rest_framework import serializers


class RetiredDeckSerializer(serializers.Serializer):
    commanderId = serializers.UUIDField(source="commander_id")
    commanderName = serializers.CharField(source="commander.name")
    source = serializers.CharField()
