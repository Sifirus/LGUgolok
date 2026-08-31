from django import forms
from rooms.models import Room


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'building', 'floor', 'capacity', 'type', 'status']
        labels = {
            'name': 'Название аудитории',
            'building': 'Корпус',
            'floor': 'Этаж',
            'capacity': 'Вместимость',
            'type': 'Тип аудитории',
            'status': 'Статус',
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Room.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Аудитория с таким названием уже существует')
        return name

    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']
        if capacity <= 0:
            raise forms.ValidationError('Вместимость должна быть больше 0')
        return capacity

    def clean_floor(self):
        floor = self.cleaned_data['floor']
        if floor < 0:
            raise forms.ValidationError('Этаж не может быть отрицательным')
        return floor
