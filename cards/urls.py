from django.urls import path

from .views import CardSyncStatusView, CardSyncView

urlpatterns = [
    path("cards/sync", CardSyncView.as_view()),
    path("cards/sync-status", CardSyncStatusView.as_view()),
]
