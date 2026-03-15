from django.contrib.auth.forms import AuthenticationForm
from django.forms import ModelForm
from django.contrib.auth import get_user_model
from django import forms

from users.models import Profile


class LoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if getattr(user, 'is_blocked', False):
            raise forms.ValidationError("Ваша запись заблокирована")
        super().confirm_login_allowed(user)



class ProfileForm(ModelForm):

    class Meta:
        model = Profile
        exclude = ('user',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


class EmailForm(ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('email',)