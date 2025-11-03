from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, PagamentoMetodoViewSet

router = DefaultRouter()
router.register(r"", UserViewSet, basename="users")
router.register(r"pagamentos", PagamentoMetodoViewSet, basename="pagamentos")

urlpatterns = router.urls
