from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy

from .forms import RegisterForm, LoginForm


# 🔥 REGISTER
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(request, "Account created successfully 🎉")
            return redirect('home')

        else:
            messages.error(request, "Please fix the errors below ❌")

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form
    })


# 🔥 LOGIN
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True   # ✅ important

    def form_valid(self, form):
        messages.success(self.request, "Login successful ✅")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password ❌")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('home')


# 🔥 LOGOUT
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully 👋")
    return redirect('home')