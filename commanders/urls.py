from django.urls import path

from .views import (
    CommanderDetailView,
    CommanderEdhrecSyncStatusView,
    CommanderEdhrecSyncView,
    CommanderListView,
)

urlpatterns = [
    path("commanders", CommanderListView.as_view()),
    path("commanders/edhrec-sync", CommanderEdhrecSyncView.as_view()),
    path("commanders/edhrec-sync-status", CommanderEdhrecSyncStatusView.as_view()),
    path("commanders/<str:id>", CommanderDetailView.as_view()),
]
