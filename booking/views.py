from django.shortcuts import render,redirect,reverse
from django.contrib import messages

from rooms.models import Room

from booking.models import Booking

from booking.forms import BookingForm
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def booking_create(request):
    pass #TODO в заявке указфываются параметры когда все обязательные заполнены, появляются свободные аудитории и оборудование, выбираем или фильтруем создаём
#TODO добавить согласование требует или нет потом когда просто создание работает