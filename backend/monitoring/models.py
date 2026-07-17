import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

class VirtualMachine(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    operating_system = models.CharField(max_length=255, blank=True, null=True)
    cpu_count = models.IntegerField(default=1)
    total_ram = models.FloatField(default=0.0) # in GB
    total_disk = models.FloatField(default=0.0) # in GB
    token = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    last_seen = models.DateTimeField(default=timezone.now)

    @property
    def status(self):
        # Online if heartbeat received within 2 minutes
        if timezone.now() - self.last_seen > timedelta(minutes=2):
            return "Offline"
        return "Online"

    def __str__(self):
        return self.hostname

class VMMetric(models.Model):
    virtual_machine = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE, related_name='metrics')
    cpu_usage = models.FloatField(default=0.0)
    ram_usage = models.FloatField(default=0.0)
    disk_usage = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.virtual_machine.hostname} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
