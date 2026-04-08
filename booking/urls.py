from django.urls import path
from booking import views

urlpatterns = [
    path('booking/create', views.booking_create, name='booking_create'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('rooms/lookup/', views.RoomLookupAPIView.as_view(), name='room_lookup_api'),
    path('users/approver-lookup/', views.ApproverLookupAPIView.as_view(), name='approver_lookup_api'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),

]
