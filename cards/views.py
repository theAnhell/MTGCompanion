from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SyncStatusSerializer
from .services import get_sync_status, sync_scryfall_cards


class CardSyncView(APIView):
    def post(self, request):
        sync_scryfall_cards()
        return Response(SyncStatusSerializer(get_sync_status()).data)


class CardSyncStatusView(APIView):
    def get(self, request):
        return Response(SyncStatusSerializer(get_sync_status()).data)
