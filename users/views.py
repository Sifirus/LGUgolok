from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.messages.views import SuccessMessageMixin

from .forms import LoginForm, ProfileForm, EmailForm
from .models import Profile


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    authentication_form = LoginForm


class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_message = 'Письмо отправлено'
    success_url = reverse_lazy('login')


class CustomPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('login')
    success_message = 'Пароль успешно сброшен'

    def form_valid(self, form):
        response = super().form_valid(form)

        user = form.user

        if getattr(user, 'must_change_password', False):
            user.must_change_password = False
            user.save()

        return response



@login_required(login_url='login')
def user_profile(request):

    profile = Profile.objects.get(user=request.user)

    profile_form = ProfileForm(instance=profile)
    email_form = EmailForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, message='Вы изменили профиль')
                return redirect('profile')
        elif 'save_email' in request.POST:
            email_form = EmailForm(request.POST, instance=request.user)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, message='Вы поменяли почту')
                return redirect('profile')
        elif 'save_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)
                if request.user.must_change_password:
                    request.user.must_change_password = False
                    request.user.save()
                messages.success(request, message='Вы поменяли пароль')
                return redirect('profile')

    context = {
        'profile': profile,
        'profile_form': profile_form,
        'email_form': email_form,
        'password_form': password_form,

    }

    return render(request, 'users/profile.html', context=context)


