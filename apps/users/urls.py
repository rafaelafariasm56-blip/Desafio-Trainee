from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.users.views import  UserRegisterViewSet, PagamentoMetodoViewSet, UserViewSet


router = routers.DefaultRouter()
router.register(r"", UserViewSet, basename="users")
router.register(r"metodoPagamento", PagamentoMetodoViewSet, basename="pagamento")

urlpatterns = [
    #Registro
    path("register/", UserRegisterViewSet.as_view({"post": "create"}), name="register"),

    #Login e Refresh
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    #Endpoints
    path("", include(router.urls)),
]
