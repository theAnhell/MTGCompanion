from django.urls import path

from .views import (
    PlayerDecksView,
    PlayerFastestToWinDecksView,
    PlayerLeastPlayedDecksView,
    PlayerLongestSincePlayedDecksView,
    PlayerSlowestToWinDecksView,
    PlayerStreaksView,
    PlayerSummaryView,
    YearlyReportView,
)

urlpatterns = [
    path("players/<str:id>/decks", PlayerDecksView.as_view()),
    path("players/<str:id>/decks/least-played", PlayerLeastPlayedDecksView.as_view()),
    path("players/<str:id>/decks/longest-since-played", PlayerLongestSincePlayedDecksView.as_view()),
    path("players/<str:id>/decks/fastest-to-win", PlayerFastestToWinDecksView.as_view()),
    path("players/<str:id>/decks/slowest-to-win", PlayerSlowestToWinDecksView.as_view()),
    path("players/<str:id>/streaks", PlayerStreaksView.as_view()),
    path("players/<str:id>/summary", PlayerSummaryView.as_view()),
    path("reports/yearly", YearlyReportView.as_view()),
]
