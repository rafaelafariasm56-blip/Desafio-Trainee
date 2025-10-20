from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomTokenObtainPairView, RegisterView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),

    #registro
    path("register/", RegisterView.as_view(), name="register"),

    #login
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),

    #token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
