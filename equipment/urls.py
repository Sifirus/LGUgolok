from django.urls import path
from equipment import views

urlpatterns = [
    path('api/equipment', views.EquipmentSearchAPIView.as_view(), name='api_equipment'),
    path('api/equipment/<int:pk>/', views.EquipmentDetailAPIView.as_view(), name='api_equipment_detail'),
    path('admin_panel/equipment/', views.equipment_list, name='equipment_list'),
    path('admin_panel/equipment/add/', views.equipment_add, name='equipment_add'),
    path('equipment/<int:equipment_id>/', views.equipment_detail, name='equipment_detail'),
    path('admin_panel/equipment/<int:equipment_id>/edit/', views.equipment_edit, name='equipment_edit'),
    path('admin_panel/equipment/<int:equipment_id>/delete/', views.equipment_delete, name='equipment_delete'),

]
