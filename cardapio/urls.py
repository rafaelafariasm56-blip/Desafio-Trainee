from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PratoViewSet, OfertaViewSet

router = DefaultRouter()
router.register("pratos", PratoViewSet, basename="pratos")
router.register("ofertas", OfertaViewSet, basename="ofertas")

urlpatterns = [
    path("", include(router.urls)),
]
