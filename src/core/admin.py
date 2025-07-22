from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'created_at', 'name', 'phone', 'telegram', 'whatsapp',
        'pickup_address', 'delivery_address', 'status'
    )
    list_filter = ('status',)
    search_fields = ('name', 'phone', 'telegram', 'pickup_address', 'delivery_address')
    ordering = ('-created_at',)
