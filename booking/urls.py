from django.urls import path
from booking import views

urlpatterns = [
    path('booking/create', views.booking_create, name='booking_create'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),

]
