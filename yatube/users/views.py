from django.views.generic import CreateView

from django.urls import reverse_lazy

from .forms import CreationForm, UserLoginForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class LoginView(CreateView):
    form_class = UserLoginForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/login.html'
