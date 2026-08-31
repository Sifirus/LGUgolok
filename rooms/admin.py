from django.contrib import admin
from rooms.models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'capacity', 'status', 'created_at',)
    list_filter = ('type', 'status',)
    search_fields = ('name',)
    ordering = ('-created_at',)
    list_per_page = 25
