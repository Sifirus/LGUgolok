from django.contrib.auth import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import ModelForm

from users.models import Profile


class LoginForm(AuthenticationForm):
    pass


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        exclude = ('user', )

