from rest_framework import serializers

from rooms.models import Room

from equipment.models import Equipment


class EquipmentFiltersSerializer(serializers.Serializer):
    is_available = serializers.BooleanField(required=False, allow_null=True)
    event_date = serializers.DateField(required=False, allow_null=True)
    event_start_time = serializers.TimeField(required=False, allow_null=True)
    event_end_time = serializers.TimeField(required=False, allow_null=True)

    search_query = serializers.CharField(required=False, allow_blank=True)
    room_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        is_available = data.get('is_available')
        event_date = data.get('event_date')
        event_start_time = data.get('event_start_time')
        event_end_time = data.get('event_end_time')
        room_id = data.get('room_id')

        if is_available and not all([event_date, event_start_time, event_end_time, is_available]):
            raise serializers.ValidationError('Введите дату события и временной промежуток чтобы получить свободные аудитории') #todo есть вариант пометить поля ошибок

        if is_available and event_start_time > event_end_time:
            raise serializers.ValidationError('Дата начала события должна быть раньше даты завершения')

        if room_id and not Room.objects.filter(id=room_id).exists():
            raise serializers.ValidationError('Комнаты с таким id не существует')

        return data


class EquipmentSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='get_type_display')
    class Meta:
        model = Equipment
        fields = ['id','room_id','inventory_number', 'type', 'name', 'model']