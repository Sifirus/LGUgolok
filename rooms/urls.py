from django.urls import path
from rooms import views

urlpatterns = [
    path('api/rooms', views.RoomSearchAPIView.as_view(), name='api_rooms'),
    path('admin_panel/rooms/', views.rooms_list, name='rooms_list'),
    path('admin_panel/rooms/add/', views.room_add, name='room_add'),
    path('admin_panel/rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('admin_panel/rooms/<int:room_id>/edit/', views.room_edit, name='room_edit'),
    path('admin_panel/rooms/<int:room_id>/delete/', views.room_delete, name='room_delete'),
]