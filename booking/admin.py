from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('room', 'event_type', 'event_date', 'event_start_time', 'event_end_time', 'status', 'initiator', 'created_at')
    list_filter = ('status', 'event_type', 'room')
    search_fields = ('room__name', 'event_type', 'initiator__email', 'comment')
    ordering = ('event_date', 'event_start_time')
    list_per_page = 25
    filter_horizontal = ('equipment',)



