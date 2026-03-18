from django.urls import path
from booking import views


urlpatterns = [
    path('booking/create', views.booking_create, name='booking_create'),
    #TODO
]