from rest_framework.response import Response
from rest_framework.views import APIView
from django.urls import reverse

class APIRootView(APIView):
    def get(self, request, format=None):
        return Response({
            "users": request.build_absolute_uri(reverse("users-list")),
            "login": request.build_absolute_uri(reverse("token_obtain_pair")),
            "refresh_token": request.build_absolute_uri(reverse("token_refresh")),
        })
