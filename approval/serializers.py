from booking.models import Booking
from rest_framework import serializers


class BookingApprovalSerializer(serializers.ModelSerializer):
    initiator_first_name = serializers.CharField(source='initiator.profile.first_name', read_only=True)
    initiator_last_name = serializers.CharField(source='initiator.profile.last_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    event_type = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'event_type', 'initiator_first_name', 'initiator_last_name', 'room_name', 'participants',
                  'event_date', 'event_start_time', 'event_end_time']


class BookingApprovalDetailSerializer(serializers.ModelSerializer):
    initiator_first_name = serializers.CharField(source='initiator.profile.first_name', read_only=True)
    initiator_last_name = serializers.CharField(source='initiator.profile.last_name', read_only=True)
    department = serializers.CharField(source='initiator.profile.department', read_only=True)
    event_type = serializers.CharField(source='get_event_type_display', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    room_building = serializers.CharField(source='room.building', read_only=True)
    room_floor = serializers.CharField(source='room.floor', read_only=True)
    room_capacity = serializers.IntegerField(source='room.capacity', read_only=True)
    equipment_list = serializers.StringRelatedField(many=True, source='equipment', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'initiator_first_name',
            'initiator_last_name',
            'department',
            'event_type',
            'event_date',
            'event_start_time',
            'event_end_time',
            'room_name',
            'room_building',
            'room_floor',
            'room_capacity',
            'participants',
            'equipment_list',
            'comment',
            'created_at'
        ]
