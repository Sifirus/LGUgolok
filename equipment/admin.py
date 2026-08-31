from django.contrib import admin
from equipment.models import Equipment


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('inventory_number', 'type', 'name', 'model', 'status', 'created_at',)
    list_filter = ('type', 'status',)
    search_fields = ('name', 'type', 'inventory_number', 'model')
    ordering = ('inventory_number',)
    list_per_page = 25
