from django.contrib import admin
from django.contrib.auth import get_user_model
from users.models import Profile


@admin.register(get_user_model())
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'created_at','must_change_password', 'is_active', 'is_blocked',)
    list_filter = ('must_change_password', 'role', 'is_active', 'is_blocked', 'created_at',)
    search_fields = ('email',)
    ordering = ('-created_at',)
    list_per_page = 25

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'avatar',)
    list_filter = ('first_name', 'last_name',)
    search_fields = ('user','first_name', 'last_name',)
    ordering = ('first_name', 'last_name',)
    list_per_page = 25