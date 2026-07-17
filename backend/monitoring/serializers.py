from rest_framework import serializers
from .models import VirtualMachine, VMMetric

class VMMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = VMMetric
        fields = ['id', 'cpu_usage', 'ram_usage', 'disk_usage', 'timestamp']

class VirtualMachineSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField()
    latest_cpu = serializers.SerializerMethodField()
    latest_ram = serializers.SerializerMethodField()
    latest_disk = serializers.SerializerMethodField()

    class Meta:
        model = VirtualMachine
        fields = [
            'id', 'hostname', 'ip_address', 'operating_system', 
            'cpu_count', 'total_ram', 'total_disk', 'last_seen', 
            'status', 'latest_cpu', 'latest_ram', 'latest_disk'
        ]

    def get_latest_cpu(self, obj):
        latest = obj.metrics.first()
        return latest.cpu_usage if latest else 0.0

    def get_latest_ram(self, obj):
        latest = obj.metrics.first()
        return latest.ram_usage if latest else 0.0

    def get_latest_disk(self, obj):
        latest = obj.metrics.first()
        return latest.disk_usage if latest else 0.0
