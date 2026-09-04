from django.urls import path

from .views import CardListView, CardSyncStatusView, CardSyncView

urlpatterns = [
    path("cards", CardListView.as_view()),
    path("cards/sync", CardSyncView.as_view()),
    path("cards/sync-status", CardSyncStatusView.as_view()),
]
