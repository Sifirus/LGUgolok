from django.urls import path
from rooms import views


urlpatterns = [
    path('api/rooms', views.RoomSearchAPIView.as_view(), name='api_rooms'),
]