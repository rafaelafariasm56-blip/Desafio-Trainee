from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FormaPagamentoViewSet

router = DefaultRouter()
router.register("formas", FormaPagamentoViewSet, basename="formas")

urlpatterns = [
    path("", include(router.urls)),
]
