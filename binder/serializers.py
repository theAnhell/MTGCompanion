from rest_framework import serializers


class BinderCardSerializer(serializers.Serializer):
    cardName = serializers.CharField(source="card_name")
    setCode = serializers.CharField(source="set_code", allow_null=True)
    collectorNumber = serializers.CharField(source="collector_number", allow_null=True)
    quantity = serializers.IntegerField()
    isFoil = serializers.BooleanField(source="is_foil")
    scryfallId = serializers.SerializerMethodField()

    def get_scryfallId(self, obj) -> str | None:
        sid = self.context.get("scryfall_ids_by_name", {}).get(obj.card_name)
        return str(sid) if sid else None
