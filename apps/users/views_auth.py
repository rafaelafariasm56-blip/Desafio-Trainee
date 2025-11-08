from django.contrib.auth.views import LoginView
from django.shortcuts import resolve_url

class CustomLoginView(LoginView):

    def get_success_url(self):
        redirect_to = self.request.POST.get('next') or self.request.GET.get('next')
        return redirect_to or resolve_url('/api/users/')

