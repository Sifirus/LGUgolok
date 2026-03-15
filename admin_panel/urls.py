from django.urls import path
from admin_panel.views import *

urlpatterns = [
    path('admin_panel/users', admin_users, name='admin_panel_users'),
]