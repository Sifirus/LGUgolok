from django.contrib import admin
from approval.models import *



@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('booking', 'approver', 'decision', 'decided_at', 'created_at')
    list_filter = ('decision', 'approver')
    search_fields = ('booking__room__name', 'approver__email')
    ordering = ('-decided_at',)
    list_per_page = 25



