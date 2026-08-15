from django.urls import path

from .views import CommanderDetailView, CommanderListView

urlpatterns = [
    path("commanders", CommanderListView.as_view()),
    path("commanders/<str:id>", CommanderDetailView.as_view()),
]
