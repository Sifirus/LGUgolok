from django.contrib import admin
from approval.models import *



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
