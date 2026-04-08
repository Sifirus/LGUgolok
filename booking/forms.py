from django import forms

import datetime

from booking.models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'event_type',
            'participants',
            'event_date',
            'event_start_time',
            'event_end_time',
            'comment',
            'room',
            'equipment'
        ]
        widgets = {
            'room': forms.HiddenInput(),
            'equipment': forms.MultipleHiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('event_date')
        start_time = cleaned_data.get('event_start_time')
        end_time = cleaned_data.get('event_end_time')
        participants = cleaned_data.get('participants')
        room = cleaned_data.get('room')

        now = datetime.datetime.now()

        if event_date and event_date < now.date():
            self.add_error('event_date', 'Дата события не может быть в прошлом')

        if event_date == now.date() and start_time:
            if start_time < now.time():
                self.add_error('event_start_time', 'Время начала не может быть в прошлом для сегодняшней даты')

        if start_time and end_time and end_time <= start_time:
            self.add_error('event_end_time', 'Время завершения должно быть позже времени начала')

        if participants and room:
            if participants > room.capacity:
                self.add_error('participants', f'В выбранной аудитории всего {room.capacity} мест')

        return cleaned_data

# TODO

from django import forms


class BookingCommentForm(forms.Form):
    text = forms.CharField(
        label='Комментарий',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Введите комментарий...',
        }),
        max_length=5000
    )