from django.urls import path
from rooms import views


urlpatterns = [
    path('api/rooms/available', views.available_rooms_json, name='available_rooms_json'),
]