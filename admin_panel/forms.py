from django import forms
from django.contrib.auth import get_user_model


VALID_ROLES = [(role.value, role.label) for role in get_user_model().Roles]


class AddUserForm(forms.Form):
    first_name = forms.CharField(max_length=20)
    last_name = forms.CharField(max_length=20)
    email = forms.EmailField()
    role = forms.ChoiceField(choices=VALID_ROLES)
    department = forms.CharField(max_length=30, required=False)

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError('Эта почта уже занята')
        return email