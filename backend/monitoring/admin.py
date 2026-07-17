from django.contrib import admin
from .models import VirtualMachine, VMMetric

@admin.register(VirtualMachine)
class VirtualMachineAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ip_address', 'status', 'last_seen')
    search_fields = ('hostname', 'ip_address')
    readonly_fields = ('token',)

@admin.register(VMMetric)
class VMMetricAdmin(admin.ModelAdmin):
    list_display = ('virtual_machine', 'cpu_usage', 'ram_usage', 'disk_usage', 'timestamp')
    list_filter = ('virtual_machine',)
    search_fields = ('virtual_machine__hostname',)
