from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rooms.models import Room
from rooms.serializers import RoomFiltersSerializer, RoomSerializer
from rooms.services.rooms_service import AvailableRoomsService, RoomsFiltersService


class RoomSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ['get']

    def get(self, request):
        serializer = RoomFiltersSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        cleaned_data = serializer.validated_data
        queryset = Room.objects.all()

        if cleaned_data.get('is_available'):
            queryset = AvailableRoomsService.get_available_rooms(
                queryset,
                cleaned_data.get('event_date'),
                cleaned_data.get('event_start_time'),
                cleaned_data.get('event_end_time')
            )

        queryset = RoomsFiltersService.apply_filters(queryset, cleaned_data)

        serializer = RoomSerializer(queryset, many=True)

        return Response(serializer.data)

