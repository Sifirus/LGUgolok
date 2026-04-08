from django import forms
from rooms.models import Room
from equipment.models import Equipment


class EquipmentForm(forms.Form):
    inventory_number = forms.CharField(max_length=10, label='Инвентарный номер')
    name = forms.CharField(max_length=100, label='Название')
    model = forms.CharField(max_length=100, label='Модель')
    type = forms.ChoiceField(choices=Equipment.TypeChoices.choices, label='Тип')
    status = forms.ChoiceField(choices=Equipment.StatusChoices.choices, label='Статус')
    is_stationary = forms.BooleanField(required=False, label='Стационарное')
    room_query = forms.CharField(required=False, label='Комната')
    room_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def clean_inventory_number(self):
        value = self.cleaned_data['inventory_number'].strip()
        qs = Equipment.objects.filter(inventory_number__iexact=value) #TODO добавить логику для instance
        if qs.exists():
            raise forms.ValidationError('Оборудование с таким инвентарным номером уже существует')
        return value

    def clean_room_id(self):
        room_id = self.cleaned_data.get('room_id')
        if not room_id:
            return None
        try:
            Room.objects.get(pk=room_id)
        except Room.DoesNotExist:
            raise forms.ValidationError('Комната не найдена')
        return room_id

    def clean(self):
        cleaned_data = super().clean()
        room_query = (cleaned_data.get('room_query') or '').strip()
        room_id = cleaned_data.get('room_id')

        if room_query and not room_id:
            raise forms.ValidationError('Выберите комнату из списка или оставьте поле пустым для склада')

        return cleaned_data