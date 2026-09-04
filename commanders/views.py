from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Commander
from .serializers import CommanderSerializer, EdhrecSyncStatusSerializer
from .services import get_edhrec_sync_status, sync_all_commander_card_stats


class CommanderListView(ListAPIView):
    serializer_class = CommanderSerializer

    def get_queryset(self):
        queryset = Commander.objects.all().order_by("name")
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class CommanderDetailView(RetrieveAPIView):
    queryset = Commander.objects.all()
    serializer_class = CommanderSerializer
    lookup_field = "id"


class CommanderEdhrecSyncView(APIView):
    def post(self, request):
        status = sync_all_commander_card_stats()
        return Response(EdhrecSyncStatusSerializer(status).data)


class CommanderEdhrecSyncStatusView(APIView):
    def get(self, request):
        return Response(EdhrecSyncStatusSerializer(get_edhrec_sync_status()).data)
