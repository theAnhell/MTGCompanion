from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Card
from .serializers import CardSummarySerializer, SyncStatusSerializer
from .services import get_sync_status, sync_scryfall_cards


class CardSyncView(APIView):
    def post(self, request):
        sync_scryfall_cards()
        return Response(SyncStatusSerializer(get_sync_status()).data)


class CardSyncStatusView(APIView):
    def get(self, request):
        return Response(SyncStatusSerializer(get_sync_status()).data)


class CardListView(ListAPIView):
    serializer_class = CardSummarySerializer

    def get_queryset(self):
        search = self.request.query_params.get("search")
        if not search:
            return Card.objects.none()
        return Card.objects.filter(name__icontains=search).order_by("name")[:20]
