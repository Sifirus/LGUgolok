from django.urls import path
from admin_panel.views import *

urlpatterns = [
    path('admin_panel/users', admin_users, name='admin_panel_users'),
    path('users/<int:user_id>', admin_user_detail, name='user_detail'),
    path('admin_panel/users/<int:user_id>/edit', admin_users_edit, name='admin_panel_user_edit'),
    path('admin_panel/users/<int:user_id>/delete', admin_users_delete, name='admin_panel_user_delete'),
    path('admin_panel/users/<int:user_id>/ban_toggle', admin_users_ban_toggle, name='admin_panel_user_ban_toggle'),
    path('admin_panel/users/add', admin_users_add, name='admin_panel_users_add'),
]
