from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from equipment.models import Equipment
from equipment.serializers import EquipmentFiltersSerializer, EquipmentSerializer
from equipment.services.equipment_service import AvailableEquipmentService, EquipmentFiltersService


class EquipmentSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ['get']

    def get(self, request):
        serializer = EquipmentFiltersSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        cleaned_data = serializer.validated_data
        queryset = Equipment.objects.all()

        if cleaned_data.get('is_available'):
            queryset = AvailableEquipmentService.get_available_equipment(
                queryset,
                cleaned_data.get('event_date'),
                cleaned_data.get('event_start_time'),
                cleaned_data.get('event_end_time')
            )

        queryset = EquipmentFiltersService.apply_filters(queryset, cleaned_data)

        serializer = EquipmentSerializer(queryset, many=True)

        return Response(serializer.data)
