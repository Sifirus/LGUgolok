import re
from rest_framework import serializers
from rooms.models import Room


class RoomFiltersSerializer(serializers.Serializer):
    is_available = serializers.BooleanField(required=False, allow_null=True)
    event_date = serializers.DateField(required=False, allow_null=True)
    event_start_time = serializers.TimeField(required=False, allow_null=True)
    event_end_time = serializers.TimeField(required=False, allow_null=True)

    capacity = serializers.IntegerField(required=False, min_value=1)
    search_query = serializers.CharField(required=False, allow_blank=True)
    equipment = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        is_available = data.get('is_available')
        event_date = data.get('event_date')
        event_start_time = data.get('event_start_time')
        event_end_time = data.get('event_end_time')

        if is_available and not all([event_date, event_start_time, event_end_time, is_available]):
            raise serializers.ValidationError(
                'Введите дату события и временной промежуток чтобы получить свободные аудитории')

        if is_available and event_start_time > event_end_time:
            raise serializers.ValidationError('Дата начала события должна быть раньше даты завершения')

        equipment = data.get('equipment')

        if equipment and not re.match('^[\w,\s]+$', equipment):
            raise serializers.ValidationError('Оборудование должно разделяться запятыми, например lab,conference,hall')

        return data


class RoomSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='get_type_display')
    type_key = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'name', 'type', 'type_key', 'capacity', 'building', 'floor']

    def get_type_key(self, obj):
        return obj.type