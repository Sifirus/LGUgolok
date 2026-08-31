from django import forms
from django.contrib.auth import get_user_model


class AddUserForm(forms.Form):
    first_name = forms.CharField(max_length=20, label='Имя')
    last_name = forms.CharField(max_length=20, label='Фамилия')
    second_name = forms.CharField(max_length=30, required=False, label='Отчество')
    email = forms.EmailField(label='Электронная почта')
    role = forms.ChoiceField(choices=get_user_model().Roles.choices, label='Роль')
    department = forms.CharField(max_length=30, required=False, label='Подразделение')

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance:
            self.fields['first_name'].initial = instance.profile.first_name
            self.fields['last_name'].initial = instance.profile.last_name
            self.fields['second_name'].initial = instance.profile.second_name
            self.fields['email'].initial = instance.email
            self.fields['role'].initial = instance.role
            self.fields['department'].initial = instance.profile.department

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = get_user_model().objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Эта почта уже занята')
        return email
