from django.urls import path
from reports import views

urlpatterns = [
    path('reports', views.reports_page, name='reports'),
    path('api/reports/overview/', views.reports_overview_data, name='reports_overview_data'),
    path('api/reports/resource/<str:resource_type>/<int:pk>/', views.reports_resource_data, name='reports_resource_data'),
    path('api/reports/search/', views.reports_search, name='reports_search'),
    path('api/reports/room/<int:room_id>/equipment/', views.room_equipment_at_datetime, name='room_equipment_at_datetime'),
    path('api/reports/export/csv/', views.export_csv, name='reports_export_csv'),
    path('api/reports/export/pdf/', views.export_pdf, name='reports_export_pdf'),
]