from django.urls import path
from notifications import views

urlpatterns = [
    path('notifications/',                  views.notification_list,  name='notification_list'),
    path('notifications/<int:pk>/read/',    views.notification_read,  name='notification_read'),
    path('notifications/read-all/',         views.notification_read_all, name='notification_read_all'),
    path('api/notifications/count/',        views.notification_count, name='notification_count'),
]