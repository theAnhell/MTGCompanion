from rest_framework import serializers


class BinderCardSerializer(serializers.Serializer):
    cardName = serializers.CharField(source="card_name")
    setCode = serializers.CharField(source="set_code", allow_null=True)
    collectorNumber = serializers.CharField(source="collector_number", allow_null=True)
    quantity = serializers.IntegerField()
    isFoil = serializers.BooleanField(source="is_foil")
