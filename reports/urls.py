from django.urls import path
from reports import views

urlpatterns = [
    path('reports/',                views.reports_page,          name='reports'),
    path('api/reports/rooms/',      views.rooms_report_data,     name='api_reports_rooms'),
    path('api/reports/equipment/',  views.equipment_report_data, name='api_reports_equipment'),
    path('api/reports/export/csv/', views.export_csv,            name='reports_export_csv'),
    path('api/reports/export/xlsx/',views.export_xlsx,           name='reports_export_xlsx'),
]