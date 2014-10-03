from inventory.models import Item, Box, Network
from django.contrib import admin


class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'minimal_quantity_in_storage', 'is_permanent', 'deleted']
    ordering = ['name']


class BoxAdmin(admin.ModelAdmin):
    list_display = ['name', 'box_type', 'network', 'deleted']
    ordering = ['name']


class NetworkAdmin(admin.ModelAdmin):
    ordering = ['name']


admin.site.register(Item, ItemAdmin)
admin.site.register(Box, BoxAdmin)
admin.site.register(Network, NetworkAdmin)
