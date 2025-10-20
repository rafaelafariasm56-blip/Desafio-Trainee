from django.urls import path
from .views import APIRootView

urlpatterns = [
    path("", APIRootView.as_view(), name="api-root"),
]
