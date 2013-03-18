from inventory.models import Item, Box
from django.contrib import admin

class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'minimal_quantity_in_storage', 'deleted']

class BoxAdmin(admin.ModelAdmin):
    list_display = ['name', 'box_type', 'deleted']

admin.site.register(Item, ItemAdmin)
admin.site.register(Box, BoxAdmin)