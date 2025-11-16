from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, LoginView, ApiRootView, PainelUsuarioView, PainelLojaView, LogoutView

app_name = "users"

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", UserViewSet.as_view({"post": "register"}), name="register"),
    path("painel/usuario/", PainelUsuarioView.as_view(), name="painel-usuario"),
    path("painel/loja/", PainelLojaView.as_view(), name="painel-loja"),
]

urlpatterns += router.urls