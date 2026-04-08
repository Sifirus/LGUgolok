from django import forms
from rooms.models import Room


class RoomForm(forms.Form):
    name = forms.CharField(max_length=100, label='Название аудитории')
    building = forms.CharField(max_length=100, label='Корпус')
    floor = forms.IntegerField(label='Этаж')
    capacity = forms.IntegerField(label='Вместимость')
    type = forms.ChoiceField(choices=Room.RoomType.choices, label='Тип аудитории')
    status = forms.ChoiceField(choices=Room.RoomStatus.choices, label='Статус')

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance:
            # Pre-populate form when editing
            self.fields['name'].initial = instance.name
            self.fields['building'].initial = instance.building
            self.fields['floor'].initial = instance.floor
            self.fields['capacity'].initial = instance.capacity
            self.fields['type'].initial = instance.type
            self.fields['status'].initial = instance.status

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Room.objects.filter(name__iexact=name)
        if self.instance:
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