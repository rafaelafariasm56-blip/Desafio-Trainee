from rest_framework import routers
from django.urls import path, include
from .views import ProdutoViewset, PerfilLojaViewset

router = routers.DefaultRouter()
router.register(r"produtos", ProdutoViewset, basename="produto")
router.register(r"lojas", PerfilLojaViewset, basename="loja")

urlpatterns = [
    path("", include(router.urls)),
]
