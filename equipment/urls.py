from django.urls import path
from equipment import views


urlpatterns = [
    path('api/equipment/available', views.available_equipment_json, name='available_equipment_json'),

]