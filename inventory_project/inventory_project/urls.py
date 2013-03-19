from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'inventory.views.home'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^logout/$', 'inventory.views.logout_view'),
    url(r'^receipt/$', 'inventory.views.receipt'),
    url(r'^reports/inventory/$', 'inventory.views.reports_inventory'),
    url(r'^reports/inventory-storage/$', 'inventory.views.reports_inventory_storage'),
    url(r'^reports/movements/$', 'inventory.views.reports_movements'),
    url(r'^requests/add/receipt$', 'inventory.views.requests_add_receipt'),
    url(r'^requests/check-availability/1/$', 'inventory.views.ajax_check_availability_receipt'),
    url(r'^requests/add/expense$', 'inventory.views.requests_add_expense'),
    url(r'^requests/check-availability/2/$', 'inventory.views.ajax_check_availability_expense'),
    url(r'^requests/create-or-update-packet/$', 'inventory.views.ajax_create_or_update_packet'),
    url(r'^requests/list/$', 'inventory.views.requests_list'),
    url(r'^requests/list-processed/$', 'inventory.views.requests_list_processed'),
    url(r'^requests/process/(?P<id>\d+)?$', 'inventory.views.requests_process'),
    url(r'^stocktaking/list/$', 'inventory.views.stocktaking_list'),
    url(r'^stocktaking/process/(?P<box_id>\d+)?$', 'inventory.views.stocktaking_process'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
