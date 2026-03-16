from django.contrib import admin

from .models import Booking, Approval, Comments


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('room', 'event_type', 'event_date', 'event_start_time', 'event_end_time', 'status', 'initiator', 'created_at')
    list_filter = ('status', 'event_type', 'room')
    search_fields = ('room__name', 'event_type', 'initiator__email', 'comment')
    ordering = ('event_date', 'event_start_time')
    list_per_page = 25
    filter_horizontal = ('equipment',)


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('booking', 'approver', 'decision', 'decided_at', 'created_at')
    list_filter = ('decision', 'approver')
    search_fields = ('booking__room__name', 'approver__email')
    ordering = ('-decided_at',)
    list_per_page = 25


@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ('text', 'approval', 'author', 'created_at')
    list_filter = ('author',)
    search_fields = ('text', 'author__email', 'approval__booking__room__name')
    ordering = ('created_at',)
    list_per_page = 25

