from django.urls import path

from .views import BinderView

urlpatterns = [
    path("players/<str:id>/binder", BinderView.as_view()),
]
