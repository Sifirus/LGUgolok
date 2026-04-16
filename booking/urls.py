from django.urls import path
from booking import views

urlpatterns = [
    path('booking/create', views.booking_create, name='booking_create'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('booking/<int:booking_id>/confirmation/', views.booking_confirmation_pdf, name='booking_confirmation_pdf'),

]
from booking import views_group

urlpatterns += [
    path('bookings/group/create/', views_group.booking_group_create, name='booking_group_create'),
    path('bookings/group/check-conflicts/', views_group.booking_group_conflicts, name='booking_group_check_conflicts'),
    path('bookings/group/submit/', views_group.booking_group_submit, name='booking_group_submit'),
    path('bookings/group/<int:group_id>/', views_group.booking_group_detail, name='booking_group_detail'),
    path('bookings/group/<int:group_id>/cancel/', views_group.booking_group_cancel, name='booking_group_cancel'),
]