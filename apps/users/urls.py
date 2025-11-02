from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, PagamentoMetodoViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')
router.register(r'pagamentos', PagamentoMetodoViewSet, basename='pagamento')

urlpatterns = [
    path('', include(router.urls)),
]