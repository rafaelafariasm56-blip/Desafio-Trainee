from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, PagamentoListCreateView, PagamentoDetailView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('pagamentos/', PagamentoListCreateView.as_view(), name='pagamentos-list'),
    path('pagamentos/<int:pk>/', PagamentoDetailView.as_view(), name='pagamentos-detail'),
]

urlpatterns += router.urls