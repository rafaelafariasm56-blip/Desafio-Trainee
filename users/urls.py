from rest_framework import routers
from django.urls import path, include
from .views import UserRegisterViewSet, PagamentoMetodoViewSet

router = routers.DefaultRouter()
router.register(r"metodoPagamento", PagamentoMetodoViewSet, basename="pagamento")

urlpatterns = [
    path("auth/register/", UserRegisterViewSet.as_view({"post": "register"}), name="register"),
    path("", include(router.urls)),
]
