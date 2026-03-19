from django.urls import path
from equipment import views


urlpatterns = [
    path('api/equipment', views.EquipmentSearchAPIView.as_view(), name='api_equipment'),

]