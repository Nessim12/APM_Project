from django.contrib import admin
from django.utils.html import format_html
from .models import VirtualMachine, VMMetric

@admin.register(VirtualMachine)
class VirtualMachineAdmin(admin.ModelAdmin):
    list_display = (
        'hostname', 'ip_address', 'operating_system', 
        'cpu_count', 'total_ram_gb', 'total_disk_gb',
        'current_cpu_display', 'current_ram_display', 'current_disk_display', 
        'status', 'last_seen', 'alerts_display'
    )
    search_fields = ('hostname', 'ip_address', 'operating_system')
    readonly_fields = ('token',)

    @admin.display(description='Total RAM (GB)')
    def total_ram_gb(self, obj):
        return f"{obj.total_ram} GB"

    @admin.display(description='Total Disk (GB)')
    def total_disk_gb(self, obj):
        return f"{obj.total_disk} GB"

    @admin.display(description='CPU Usage (%)')
    def current_cpu_display(self, obj):
        return f"{obj.current_cpu}%"

    @admin.display(description='RAM Usage (%)')
    def current_ram_display(self, obj):
        return f"{obj.current_ram}%"

    @admin.display(description='Disk Usage (%)')
    def current_disk_display(self, obj):
        return f"{obj.current_disk}%"

    @admin.display(description='Alerts')
    def alerts_display(self, obj):
        alerts = obj.alerts
        if alerts == "Normal":
            return format_html('<span style="color: green; font-weight: bold;">Normal</span>')
        elif alerts == "No data":
            return format_html('<span style="color: gray;">No data</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">🚨 {}</span>', alerts)

@admin.register(VMMetric)
class VMMetricAdmin(admin.ModelAdmin):
    list_display = ('virtual_machine', 'cpu_usage', 'ram_usage', 'disk_usage', 'timestamp')
    list_filter = ('virtual_machine',)
    search_fields = ('virtual_machine__hostname',)
